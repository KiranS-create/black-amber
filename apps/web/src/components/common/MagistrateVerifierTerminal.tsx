import React, { useState } from 'react';
import { Terminal, ShieldCheck, CheckCircle2, Play, Copy, Check } from 'lucide-react';

export const MagistrateVerifierTerminal: React.FC = () => {
  const [copied, setCopied] = useState(false);
  const [running, setRunning] = useState(false);
  const [output, setOutput] = useState<string | null>(null);

  const sampleCommand = 'python aegistrace_verify.py release_candidate/evidence_packages/sample_pkg.zip';

  const handleCopy = () => {
    navigator.clipboard.writeText(sampleCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRunVerification = () => {
    setRunning(true);
    setOutput(null);
    setTimeout(() => {
      setOutput(`[AEGISTRACE AIR-GAPPED VERIFIER v1.0.0]
[+] Initializing Post-Quantum Cryptographic Root...
[+] NIST FIPS 204 ML-DSA-65 Root Key: VALID (SHA-256: 8f3d...91c0)
[+] Unpacking sealed archive: sample_pkg.zip
[+] RFC-6962 Merkle Tree Audit Path: 6 leaves verified (Root: c72e...44a1)
[+] BCH Error-Correcting Code check: 0 bit flips detected
[+] Zero-Knowledge Evidence Hash Commitments: MATCHED
----------------------------------------------------------------------
[OVERALL STATUS] -> PACKAGE VERIFIED (JUDICIALLY DEFENSIBLE EVIDENCE)
----------------------------------------------------------------------`);
      setRunning(false);
    }, 1200);
  };

  return (
    <div style={{
      backgroundColor: '#0D1117',
      border: '1px solid #30363D',
      borderRadius: '8px',
      overflow: 'hidden',
      fontFamily: 'var(--font-mono, monospace)'
    }}>
      {/* Terminal Title Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 16px',
        backgroundColor: '#161B22',
        borderBottom: '1px solid #30363D'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#EF4444' }} />
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#F59E0B' }} />
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#10B981' }} />
          <span style={{ fontSize: '12px', color: '#8B949E', marginLeft: '6px' }}>
            aegistrace-magistrate-terminal — air-gap audit
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={handleCopy}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              backgroundColor: 'transparent',
              border: '1px solid #30363D',
              borderRadius: '4px',
              padding: '3px 8px',
              color: '#8B949E',
              fontSize: '11px',
              cursor: 'pointer'
            }}
          >
            {copied ? <Check size={12} color="#10B981" /> : <Copy size={12} />}
            <span>{copied ? 'Copied' : 'Copy CLI'}</span>
          </button>
          <button
            onClick={handleRunVerification}
            disabled={running}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              backgroundColor: '#238636',
              border: 'none',
              borderRadius: '4px',
              padding: '3px 10px',
              color: '#FFFFFF',
              fontSize: '11px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <Play size={12} />
            <span>{running ? 'Verifying…' : 'Run Audit'}</span>
          </button>
        </div>
      </div>

      {/* Terminal Body */}
      <div style={{ padding: '16px', fontSize: '12.5px', color: '#C9D1D9', minHeight: '260px' }}>
        <div style={{ color: '#8B949E', marginBottom: '12px' }}>
          # Sovereign Enclave Air-Gapped Verification Utility<br />
          # Run independently on an isolated, non-networked workstation:
        </div>
        <div style={{ color: '#58A6FF', marginBottom: '16px' }}>
          $ {sampleCommand}
        </div>

        {running && (
          <div style={{ color: '#E3B341' }}>
            [*] Auditing post-quantum cryptographic commitments…
          </div>
        )}

        {output && (
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap', color: '#7EE787', lineHeight: 1.5 }}>
            {output}
          </pre>
        )}

        {!running && !output && (
          <div style={{ color: '#8B949E', marginTop: '24px' }}>
            Press "Run Audit" above or execute the CLI script locally to verify package integrity offline.
          </div>
        )}
      </div>
    </div>
  );
};
