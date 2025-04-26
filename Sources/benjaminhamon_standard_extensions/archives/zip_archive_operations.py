# cspell:words compresslevel

import logging
import os
from typing import List, Optional, Tuple
import zipfile

from benjaminhamon_standard_extensions.archives.archive_operations_base import ArchiveOperationsBase


logger = logging.getLogger("ArchiveOperations")


class ZipArchiveOperations(ArchiveOperationsBase):


    def __init__(self, compression: int = zipfile.ZIP_STORED, compression_level: Optional[int] = None) -> None:
        super().__init__()

        self._compression = compression
        self._compression_level = compression_level


    def get_file_extension(self) -> str:
        return ".zip"


    def _create_implementation(self, archive_path: str, mapping_collection: List[Tuple[str, str]]) -> None:
        with zipfile.ZipFile(archive_path + ".tmp", mode = "w", compression = self._compression, compresslevel = self._compression_level) as archive_file:
            for source, destination in mapping_collection:
                destination = os.path.normpath(destination).replace("\\", "/")
                if self.log_individual_entries:
                    logger.debug("+ '%s' => '%s'", source, destination)
                archive_file.write(source, destination)
        os.replace(archive_path + ".tmp", archive_path)


    def list_files(self, archive_path: str)-> List[str]:
        with zipfile.ZipFile(archive_path, mode = "r") as archive_file:
            return [ x for x in archive_file.namelist() if not x.replace("\\", "/").endswith('/') ]


    def verify(self, archive_path: str) -> None:
        logger.debug("Verifying archive '%s'", archive_path)

        with zipfile.ZipFile(archive_path, mode = "r") as archive_file:
            if archive_file.testzip():
                raise RuntimeError("Archive '%s' is corrupted" % archive_path)


    def _extract_implementation(self, archive_path: str, extraction_directory: str, file_collection: List[str], *, simulate: bool = False) -> None:
        logger.debug("Extracting files to '%s'", extraction_directory)

        with zipfile.ZipFile(archive_path, mode = "r") as archive_file:
            for source in file_collection:
                destination = os.path.normpath(os.path.join(extraction_directory, source))

                if self.log_individual_entries:
                    logger.debug("+ '%s' => '%s'", source, destination)
                if not simulate:
                    archive_file.extract(source, extraction_directory)
