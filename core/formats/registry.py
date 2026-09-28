"""
SIH26237 - Multi-Format Adapter Capability Registry.
Maintains central catalog of all format adapters and provides authoritative capability queries:
'What forensic guarantees do we have for this exact file type?'
"""

from typing import Dict, List, Optional, Tuple, Any
from core.formats.models import (
    FormatCapabilities,
    FormatIdentificationResult,
    FormatTier,
    CapabilityState,
    SecurityFailureClass,
    FormatSecurityException
)
from core.formats.base import FileTypeAdapter
from core.formats.detector import FormatDetector


class FormatAdapterRegistry:
    """
    Thread-safe central registry managing all format adapters.
    """
    _instance: Optional['FormatAdapterRegistry'] = None

    def __init__(self):
        self._adapters_by_format: Dict[str, FileTypeAdapter] = {}
        self._adapters_by_ext: Dict[str, FileTypeAdapter] = {}
        self._adapters_by_mime: Dict[str, FileTypeAdapter] = {}

    @classmethod
    def get_instance(cls) -> 'FormatAdapterRegistry':
        if cls._instance is None:
            cls._instance = FormatAdapterRegistry()
            cls._instance._register_default_adapters()
        return cls._instance

    def register_adapter(self, adapter: FileTypeAdapter) -> None:
        """Registers a format adapter and indexes it by format name, extensions, and MIME types."""
        caps = adapter.get_capabilities()
        fmt_name = caps.format_name.upper()
        self._adapters_by_format[fmt_name] = adapter

        for ext in caps.supported_extensions:
            self._adapters_by_ext[ext.lower().lstrip(".")] = adapter

        for mime in caps.mime_types:
            self._adapters_by_mime[mime.lower()] = adapter

    def get_adapter(self, format_name: str) -> Optional[FileTypeAdapter]:
        """Retrieves adapter by canonical format name (e.g. 'DOCX', 'PDF')."""
        return self._adapters_by_format.get(format_name.upper())

    def get_adapter_for_extension(self, ext: str) -> Optional[FileTypeAdapter]:
        """Retrieves adapter by file extension."""
        return self._adapters_by_ext.get(ext.lower().lstrip("."))

    def get_adapter_for_mime(self, mime: str) -> Optional[FileTypeAdapter]:
        """Retrieves adapter by MIME type."""
        return self._adapters_by_mime.get(mime.lower())

    def detect_and_get_adapter(
        self,
        data: bytes,
        filename: Optional[str] = None,
        declared_mime: Optional[str] = None
    ) -> Tuple[FileTypeAdapter, FormatIdentificationResult]:
        """
        Sniffs format from magic bytes and returns the matching adapter and identification result.
        """
        id_result = FormatDetector.identify_format(data, filename, declared_mime)
        adapter = self.get_adapter(id_result.detected_format)

        if not adapter:
            # Fallback check by extension or generic tier-3 adapter
            adapter = self.get_adapter_for_extension(id_result.extension)

        if not adapter:
            raise FormatSecurityException(
                failure_class=SecurityFailureClass.UNSUPPORTED_FORMAT,
                message=f"No format adapter registered for detected format: '{id_result.detected_format}'"
            )

        return adapter, id_result

    def query_guarantees(self, format_or_ext: str) -> FormatCapabilities:
        """
        Answers: 'What forensic guarantees do we have for this exact file type?'
        """
        cleaned = format_or_ext.upper().lstrip(".")
        adapter = self.get_adapter(cleaned) or self.get_adapter_for_extension(cleaned.lower())
        if adapter:
            return adapter.get_capabilities()

        # Return default unsupported descriptor
        return FormatCapabilities(
            format_name=cleaned,
            primary_extension=cleaned.lower(),
            supported_extensions=[cleaned.lower()],
            mime_types=["application/octet-stream"],
            tier=FormatTier.TIER_3,
            capability_state=CapabilityState.UNSUPPORTED,
            carrier_mode=CarrierMode.UNSUPPORTED if 'CarrierMode' in globals() else "UNSUPPORTED",  # type: ignore
            can_inspect_structure=False,
            can_canonicalize=False,
            can_render_visual_carrier=False,
            can_embed_watermark=False,
            can_extract_watermark=False,
            can_transform_robustness_test=False,
            description="Format not registered in AegisTrace capability registry.",
            known_limitations=["No adapter implementation available"]
        )

    def get_all_capabilities(self) -> Dict[str, FormatCapabilities]:
        """Returns capability descriptors for all registered adapters."""
        return {
            fmt: adapter.get_capabilities()
            for fmt, adapter in self._adapters_by_format.items()
        }

    def _register_default_adapters(self) -> None:
        """Lazy-loads and registers all default Tier 1, Tier 2, and Tier 3 adapters."""
        from core.formats.adapters.pdf import PdfFormatAdapter
        from core.formats.adapters.docx import DocxFormatAdapter
        from core.formats.adapters.pptx import PptxFormatAdapter
        from core.formats.adapters.xlsx import XlsxFormatAdapter
        from core.formats.adapters.raster import RasterImageFormatAdapter
        from core.formats.adapters.text import TextFormatAdapter
        from core.formats.adapters.csv import CsvFormatAdapter
        from core.formats.adapters.rtf import RtfFormatAdapter
        from core.formats.adapters.opendocument import OpenDocumentFormatAdapter
        from core.formats.adapters.tier3_modeled import (
            ZipContainerFormatAdapter,
            VideoFormatAdapter,
            AudioFormatAdapter,
            CadFormatAdapter,
            ScientificFormatAdapter
        )

        # Tier 1 Adapters
        self.register_adapter(PdfFormatAdapter())
        self.register_adapter(DocxFormatAdapter())
        self.register_adapter(PptxFormatAdapter())
        self.register_adapter(XlsxFormatAdapter())
        self.register_adapter(RasterImageFormatAdapter("PNG", ["png"], ["image/png"]))
        self.register_adapter(RasterImageFormatAdapter("JPEG", ["jpg", "jpeg", "jpe", "jfif"], ["image/jpeg"]))

        # Tier 2 Adapters
        self.register_adapter(TextFormatAdapter())
        self.register_adapter(CsvFormatAdapter())
        self.register_adapter(RtfFormatAdapter())
        self.register_adapter(OpenDocumentFormatAdapter("ODT", ["odt"], ["application/vnd.oasis.opendocument.text"]))
        self.register_adapter(OpenDocumentFormatAdapter("ODS", ["ods"], ["application/vnd.oasis.opendocument.spreadsheet"]))
        self.register_adapter(OpenDocumentFormatAdapter("ODP", ["odp"], ["application/vnd.oasis.opendocument.presentation"]))

        # Tier 3 Modeled Adapters
        self.register_adapter(ZipContainerFormatAdapter())
        self.register_adapter(VideoFormatAdapter())
        self.register_adapter(AudioFormatAdapter())
        self.register_adapter(CadFormatAdapter())
        self.register_adapter(ScientificFormatAdapter())


default_adapter_registry = FormatAdapterRegistry.get_instance()


def get_format_registry() -> FormatAdapterRegistry:
    """Returns the singleton instance of FormatAdapterRegistry."""
    return FormatAdapterRegistry.get_instance()
