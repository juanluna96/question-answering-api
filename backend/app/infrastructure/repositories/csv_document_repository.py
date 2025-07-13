import pandas as pd
import asyncio
import os
from typing import List, Optional
from ...domain.entities.document import Document
from ...domain.ports.document_repository import DocumentRepository

class CSVDocumentRepository(DocumentRepository):
    """Adaptador para cargar documentos desde archivos CSV usando pandas"""
    
    def __init__(self, max_file_size_mb: int = 50):
        """Inicializa el repositorio
        
        Args:
            max_file_size_mb: Tamaño máximo del archivo en MB
        """
        self.max_file_size_mb = max_file_size_mb
    
    async def load_documents(self, file_path: str) -> List[Document]:
        """Carga documentos desde un archivo CSV
        
        Args:
            file_path: Ruta al archivo CSV
            
        Returns:
            Lista de documentos cargados
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el formato del CSV es incorrecto o el archivo es muy grande
        """
        # Validar archivo
        self._validate_file(file_path)
        
        try:
            # Ejecutar la lectura del CSV en un hilo separado para no bloquear
            loop = asyncio.get_event_loop()
            documents = await loop.run_in_executor(None, self._read_csv_with_pandas, file_path)
            
        except Exception as e:
            raise ValueError(f"Error al leer el archivo CSV: {str(e)}")
            
        return documents
    
    def _validate_file(self, file_path: str) -> None:
        """Valida el archivo CSV
        
        Args:
            file_path: Ruta al archivo CSV
            
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo es muy grande
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No se encontró el archivo CSV: {file_path}")
        
        # Verificar tamaño del archivo
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            raise ValueError(
                f"El archivo es muy grande ({file_size_mb:.1f}MB). "
                f"Máximo permitido: {self.max_file_size_mb}MB"
            )
    
    def _read_csv_with_pandas(self, file_path: str) -> List[Document]:
        """Lee el archivo CSV usando pandas
        
        Args:
            file_path: Ruta al archivo CSV
            
        Returns:
            Lista de documentos
        """
        # Leer CSV con pandas - detecta automáticamente separadores
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            # Intentar con diferentes encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("No se pudo decodificar el archivo CSV")
        except pd.errors.EmptyDataError:
            raise ValueError("El archivo CSV está vacío")
        except pd.errors.ParserError as e:
            raise ValueError(f"Error al parsear el archivo CSV: {str(e)}")
        
        # Validar que el DataFrame no esté vacío
        if df.empty:
            raise ValueError("El archivo CSV no contiene datos válidos")
        
        # Limpiar datos
        df = self._clean_dataframe(df)
        
        # Identificar columna de contenido
        content_column = self._identify_content_column(df)
        
        documents = []
        for idx, (_, row) in enumerate(df.iterrows()):
            content = self._extract_content_from_row(row, content_column)
            
            if content and len(content.strip()) > 0:
                # idx ya es un entero desde enumerate
                row_num = idx + 1
                
                # Crear metadatos excluyendo la columna de contenido
                metadata = {
                    "row_number": row_num,
                    "source_file": file_path,
                    **{k: str(v) for k, v in row.items() 
                       if k != content_column and not pd.isna(v)}
                }
                
                document = Document(
                    id=f"doc_{row_num}",
                    content=content,
                    metadata=metadata
                )
                documents.append(document)
        
        return documents
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia el DataFrame
        
        Args:
            df: DataFrame a limpiar
            
        Returns:
            DataFrame limpio
        """
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # Convertir a string y limpiar espacios
        for col in df.columns:
            if df[col].dtype == 'object':
                # Reemplazar NaN con string vacío antes de convertir
                df[col] = df[col].fillna('')
                df[col] = df[col].astype(str).str.strip()
                # Limpiar valores que se convirtieron a 'nan' como string
                df[col] = df[col].replace(['nan', 'None', 'null'], '')
        
        return df
    
    def _identify_content_column(self, df: pd.DataFrame) -> str:
        """Identifica la columna principal de contenido
        
        Args:
            df: DataFrame del CSV
            
        Returns:
            Nombre de la columna de contenido
        """
        # Buscar columnas comunes para contenido
        content_keywords = ['content', 'text', 'description', 'body', 'message', 'document', 'texto', 'contenido']
        
        for keyword in content_keywords:
            for col in df.columns:
                if keyword.lower() in col.lower():
                    return col
        
        # Si no encuentra, usar la columna con más texto promedio
        text_lengths = {}
        for col in df.columns:
            if df[col].dtype == 'object':
                # Calcular longitud promedio excluyendo valores vacíos
                non_empty_values = df[col].astype(str).str.strip()
                non_empty_values = non_empty_values[non_empty_values != '']
                if len(non_empty_values) > 0:
                    avg_length = non_empty_values.str.len().mean()
                    text_lengths[col] = avg_length
        
        if text_lengths:
            return str(max(text_lengths, key=lambda x: text_lengths[x]))
        
        # Como último recurso, usar la primera columna
        if len(df.columns) > 0:
            return str(df.columns[0])
        else:
            raise ValueError("El DataFrame no tiene columnas válidas")
    
    def _extract_content_from_row(self, row: pd.Series, content_column: str) -> str:
        """Extrae el contenido principal de una fila
        
        Args:
            row: Fila del DataFrame
            content_column: Nombre de la columna de contenido
            
        Returns:
            Contenido extraído y limpio
        """
        content = str(row[content_column]) if row[content_column] is not None and str(row[content_column]) != 'nan' else ""
        
        # Si la columna principal está vacía, intentar con otras columnas
        if not content or content.strip() == "" or content == "nan":
            for col in row.index:
                if col != content_column and row[col] is not None and str(row[col]) != 'nan':
                    potential_content = str(row[col]).strip()
                    if len(potential_content) > 10:  # Contenido mínimo
                        content = potential_content
                        break
        
        return content.strip()
    
    def get_dataframe(self, file_path: str) -> pd.DataFrame:
        """Obtiene el DataFrame completo (útil para análisis y búsquedas futuras)
        
        Args:
            file_path: Ruta al archivo CSV
            
        Returns:
            DataFrame con los datos del CSV
        """
        self._validate_file(file_path)
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("No se pudo decodificar el archivo CSV")
        except pd.errors.EmptyDataError:
            raise ValueError("El archivo CSV está vacío")
        except pd.errors.ParserError as e:
            raise ValueError(f"Error al parsear el archivo CSV: {str(e)}")
        
        if df.empty:
            raise ValueError("El archivo CSV no contiene datos válidos")
        
        return self._clean_dataframe(df)