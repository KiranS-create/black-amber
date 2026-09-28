import os
import sys
import io
import zipfile

sys.path.insert(0, os.path.abspath('.'))

from tests.formats.fixtures import (
    create_minimal_pdf_bytes,
    create_minimal_docx_bytes,
    create_minimal_pptx_bytes,
    create_minimal_xlsx_bytes,
    create_minimal_png_bytes,
    create_minimal_jpeg_bytes,
)

out_dir = os.path.join('tests', 'fixtures', 'samples')
os.makedirs(out_dir, exist_ok=True)

fixtures = {
    'sample.pdf': create_minimal_pdf_bytes('AegisTrace Master PDF', 'Confidential Forensic Document'),
    'sample.docx': create_minimal_docx_bytes('AegisTrace Master DOCX', 'Confidential Forensic Document'),
    'sample.pptx': create_minimal_pptx_bytes('AegisTrace Master PPTX', 'Confidential Presentation'),
    'sample.xlsx': create_minimal_xlsx_bytes('AegisTrace Master XLSX'),
    'sample.png': create_minimal_png_bytes(width=256, height=256),
    'sample.jpg': create_minimal_jpeg_bytes(width=256, height=256),
    'empty_file.pdf': b'',
    'corrupt_file.pdf': b'%PDF-1.4 CORRUPT HEADER TRUNCATED AND MALFORMED',
    'malicious.exe': b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00',
    'oversized_file.pdf': b'%PDF-1.4\n' + (b'0' * (51 * 1024 * 1024)), # 51 MB > 50 MB limit
}

for name, data in fixtures.items():
    p = os.path.join(out_dir, name)
    with open(p, 'wb') as f:
        f.write(data)
    print(f'Wrote {name} ({len(data)} bytes)')

# Valid package
valid_buf = io.BytesIO()
with zipfile.ZipFile(valid_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('manifest.json', '{"version": "1.0.0", "package_id": "PKG-VALID-001", "status": "VERIFIED"}')
    zf.writestr('evidence_receipt.txt', 'Cryptographically sealed evidence package.')
with open(os.path.join(out_dir, 'valid_package.zip'), 'wb') as f:
    f.write(valid_buf.getvalue())
print('Wrote valid_package.zip')

# Tampered package
tampered_buf = io.BytesIO()
with zipfile.ZipFile(tampered_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('manifest.json', '{"version": "1.0.0", "package_id": "PKG-TAMPERED-001", "status": "TAMPERED", "tampered": true}')
    zf.writestr('corrupt_evidence.bin', b'TAMPERED_BYTE_PAYLOAD')
with open(os.path.join(out_dir, 'tampered_package.zip'), 'wb') as f:
    f.write(tampered_buf.getvalue())
print('Wrote tampered_package.zip')
