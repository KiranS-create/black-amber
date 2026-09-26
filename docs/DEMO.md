# End-to-End Demo Guide

## Executing the CLI Demo
Run the automated end-to-end demo from the workspace root:

```powershell
python demo/end_to_end.py
```

## Demo Flow
1. **Document Generation**: Generates a standard confidential PDF.
2. **Recipient Enrollment**: Creates cryptographic identities for Alice, Bob, and Charlie.
3. **Encrypted Distribution**: Generates individual packages with ML-KEM-768 key encapsulation.
4. **Recipient Decryption**: Bob decrypts using his private key and generates a signed provenance event logged to the tamper-evident ledger.
5. **Leak Analysis**: Analyzes the leaked document and accurately attributes Bob with HIGH confidence.
6. **Adversarial Verification Suite**:
   - Validates Alice leak $\rightarrow$ Alice
   - Validates Bob leak $\rightarrow$ Bob
   - Validates Charlie leak $\rightarrow$ Charlie
   - Validates unwatermarked raw leak $\rightarrow$ ABSTAIN (`NO_SIGNAL`)
   - Validates forged HMAC token $\rightarrow$ ABSTAIN (`INSUFFICIENT_EVIDENCE`)
   - Validates tampered recipient frame $\rightarrow$ ABSTAIN (`INSUFFICIENT_EVIDENCE`)
   - Validates mismatched release scope $\rightarrow$ ABSTAIN (`CONFLICT`)

## Running Pytest Suite
```powershell
python -m pytest -v
```
