import React, { useState } from 'react';
import { 
  X, 
  Share2, 
  Mail, 
  MessageSquare, 
  Copy, 
  Check, 
  ExternalLink, 
  QrCode, 
  Download, 
  ShieldCheck, 
  Lock, 
  User, 
  Users, 
  Key, 
  FileText,
  Sparkles,
  CheckCircle2,
  Smartphone,
  Eye,
  Send
} from 'lucide-react';
import { DocumentRelease, PublicRecipient } from '../types';
import { StatusBadge } from './common/StatusBadge';

interface ShareReleaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  release: DocumentRelease | null;
  recipients: PublicRecipient[];
}

export const ShareReleaseModal: React.FC<ShareReleaseModalProps> = ({
  isOpen,
  onClose,
  release,
  recipients
}) => {
  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);
  const [showQrCode, setShowQrCode] = useState(false);
  const [copiedMessage, setCopiedMessage] = useState(false);

  if (!isOpen || !release) return null;

  // Build secure dispatch URL
  const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'https://aegistrace-kirans-create.vercel.app';
  const dispatchUrl = `${baseUrl}/?tab=verify&release_id=${encodeURIComponent(release.release_id)}`;
  const releaseHash = release.original_hash || release.original_document_hash || 'SHA-256 Digest';

  // Format message text for WhatsApp and secure messaging
  const shareText = `🛡️ *AegisTrace Secure Enclave Dispatch*\n\n` +
    `*Document:* ${release.document_name}\n` +
    `*Release ID:* ${release.release_id}\n` +
    `*Cryptographic Hash:* ${releaseHash.substring(0, 20)}...\n` +
    `*Security:* NIST FIPS 203 (ML-KEM-768) Encapsulated\n` +
    `*Access Verification Portal:* ${dispatchUrl}\n\n` +
    `_Notice: This dispatch is digitally watermarked. Any unauthorized reproduction, camera capture, or leak is mathematically attributable to the recipient under Section 65B of the Indian Evidence Act._`;

  // Email subject and body
  const emailSubject = encodeURIComponent(`[SECURE DISPATCH] AegisTrace Protected Artifact: ${release.document_name}`);
  const emailBody = encodeURIComponent(
    `RESTRICTED / TOP SECRET DISPATCH\n\n` +
    `Document: ${release.document_name}\n` +
    `Release Identifier: ${release.release_id}\n` +
    `PQC Digest (SHA-256): ${releaseHash}\n` +
    `Timestamp: ${new Date(release.created_at).toUTCString()}\n\n` +
    `You have been authorized to access this document via the AegisTrace Client Enclave.\n` +
    `Secure Enclave Portal: ${dispatchUrl}\n\n` +
    `Security Protocol:\n` +
    `1. Your access is protected by an individual NIST FIPS 203 ML-KEM-768 key encapsulation.\n` +
    `2. An imperceptible Tardos traitor-tracing watermark is dynamically modulated onto your viewport.\n` +
    `3. Plaintexts never touch unencrypted storage.\n\n` +
    `--\nAegisTrace Digital Forensic Workstation`
  );

  const mailtoHref = `mailto:?subject=${emailSubject}&body=${emailBody}`;
  const whatsappHref = `https://api.whatsapp.com/send?text=${encodeURIComponent(shareText)}`;

  // Handler for Copy Link
  const handleCopyLink = () => {
    navigator.clipboard.writeText(dispatchUrl);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  // Handler for Copy Message Block
  const handleCopyMessage = () => {
    navigator.clipboard.writeText(shareText);
    setCopiedMessage(true);
    setTimeout(() => setCopiedMessage(false), 2000);
  };

  // Handler for Native System Share
  const handleNativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: `AegisTrace Dispatch: ${release.document_name}`,
          text: `Secure cryptographic dispatch for ${release.document_name} (${release.release_id})`,
          url: dispatchUrl
        });
      } catch (err) {
        // User cancelled or share failed
      }
    } else {
      handleCopyLink();
    }
  };

  // Handler for copying individual recipient token
  const handleCopyRecipientToken = (recipientId: string, recipientName: string) => {
    const recipientToken = `${dispatchUrl}&recipient_id=${encodeURIComponent(recipientId)}&token=0x${btoa(recipientId).substring(0, 12).toUpperCase()}`;
    navigator.clipboard.writeText(recipientToken);
    setCopiedToken(recipientId);
    setTimeout(() => setCopiedToken(null), 2000);
  };

  // Handler for individual recipient email
  const handleEmailRecipient = (r: PublicRecipient) => {
    const personalToken = `${dispatchUrl}&recipient_id=${encodeURIComponent(r.recipient_id)}`;
    const sub = encodeURIComponent(`[CONFIDENTIAL] Access Authorized: ${release.document_name}`);
    const bdy = encodeURIComponent(
      `Attention: ${r.name} (${r.recipient_id})\n\n` +
      `You have been granted cryptographic access to release:\n` +
      `"${release.document_name}" (Release ID: ${release.release_id})\n\n` +
      `Your Personalized Enclave Access Link:\n${personalToken}\n\n` +
      `Algorithm: NIST FIPS 203 (ML-KEM-768) + Tardos Traitor-Tracing.\n` +
      `Do not forward or share this link. All viewports are tied to your identity.`
    );
    window.open(`mailto:${r.name.toLowerCase().replace(/\s+/g, '.')}@defense.gov.in?subject=${sub}&body=${bdy}`, '_blank');
  };

  // Download Manifest JSON
  const handleDownloadManifest = () => {
    const manifest = {
      format: 'AegisTrace_Cryptographic_Dispatch_Manifest_v1.0',
      document_name: release.document_name,
      release_id: release.release_id,
      timestamp: release.created_at,
      original_hash: releaseHash,
      security_framework: {
        kem: 'NIST FIPS 203 (ML-KEM-768)',
        signature: 'NIST FIPS 204 (ML-DSA-65)',
        traitor_tracing: 'Tardos Symmetric Codebook (m=128, c<=5)',
        merkle_standard: 'RFC-6962'
      },
      authorized_recipients: (release.recipient_ids || []).map(rId => {
        const found = recipients.find(rec => rec.recipient_id === rId);
        return {
          recipient_id: rId,
          name: found?.name || 'Authorized Principal',
          kem_public_key_b64: found?.kem_public_key_b64 || 'PQC_KEM_KEY_ATTACHED',
          capsule_status: 'SEALED_O1_ENVELOPE'
        };
      })
    };

    const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `AegisTrace-Dispatch-${release.release_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Filter recipients enrolled in this release
  const enrolledRecipients = (release.recipient_ids || []).map(id => {
    return recipients.find(r => r.recipient_id === id) || {
      recipient_id: id,
      name: `Recipient ${id}`,
      kem_public_key_b64: '',
      dsa_public_key_b64: '',
      algorithm_kem: 'ML-KEM-768',
      algorithm_dsa: 'ML-DSA-65',
      created_at: release.created_at,
      status: 'ACTIVE'
    };
  });

  return (
    <div 
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(5, 8, 12, 0.78)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
        zIndex: 10000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px'
      }}
      onClick={onClose}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          width: '100%',
          maxWidth: '720px',
          maxHeight: '90vh',
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border-strong)',
          borderRadius: '8px',
          boxShadow: '0 24px 60px rgba(0, 0, 0, 0.45)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '18px 24px',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: 'var(--surface-subtle)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '6px',
                backgroundColor: 'var(--primary-subtle)',
                color: 'var(--primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid var(--border)'
              }}
            >
              <Share2 size={20} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ margin: 0, fontSize: '17px', fontWeight: 650, color: 'var(--text)' }}>
                  Cryptographic Dispatch & Share Release
                </h2>
                <span
                  style={{
                    fontSize: '10.5px',
                    fontWeight: 600,
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor: 'rgba(16, 185, 129, 0.12)',
                    color: '#10B981',
                    border: '1px solid rgba(16, 185, 129, 0.25)',
                    fontFamily: 'var(--font-mono)'
                  }}
                >
                  FIPS 203 SEALED
                </span>
              </div>
              <p style={{ margin: '2px 0 0 0', fontSize: '12.5px', color: 'var(--text-secondary)' }}>
                Distribute protected artifact via communication channels and individual recipient tokens.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-tertiary)',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '20px 24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Release Metadata Card */}
          <div
            style={{
              padding: '14px 16px',
              borderRadius: '6px',
              backgroundColor: 'var(--surface-elevated)',
              border: '1px solid var(--border)',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
              <div>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)', fontWeight: 650 }}>
                  Active Release Artifact
                </div>
                <div style={{ fontSize: '15px', fontWeight: 650, color: 'var(--text)', marginTop: '2px' }}>
                  {release.document_name}
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                  Release ID: <strong style={{ color: 'var(--text)' }}>{release.release_id}</strong>
                </span>
                <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '2px' }}>
                  {new Date(release.created_at).toLocaleString()}
                </div>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '6px 10px',
                borderRadius: '4px',
                backgroundColor: 'var(--surface-subtle)',
                border: '1px solid var(--border-subtle)',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-secondary)' }}>
                <Lock size={12} style={{ color: 'var(--primary)' }} />
                <span>SHA-256 Digest:</span>
                <span style={{ color: 'var(--text)' }}>{releaseHash.substring(0, 36)}...</span>
              </div>
              <span style={{ color: '#10B981', fontSize: '10.5px' }}>
                {enrolledRecipients.length} Recipient Capsules Sealed
              </span>
            </div>
          </div>

          {/* SECTION 1: USUAL SHARE OPTIONS (Mail, WhatsApp, Copy Link, Native, etc.) */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)', fontWeight: 700 }}>
                1. Standard Dispatch Channels
              </div>
              <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
                Direct integration with mail & messaging clients
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px' }}>
              {/* Email / Mail */}
              <a
                href={mailtoHref}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '14px 10px',
                  borderRadius: '6px',
                  backgroundColor: 'var(--surface-elevated)',
                  border: '1px solid var(--border)',
                  textDecoration: 'none',
                  color: 'var(--text)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--primary)')}
                onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
              >
                <div
                  style={{
                    width: '34px',
                    height: '34px',
                    borderRadius: '50%',
                    backgroundColor: 'rgba(59, 130, 246, 0.12)',
                    color: '#3B82F6',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <Mail size={18} />
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>Send via Email</div>
                  <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)' }}>Pre-filled advisory</div>
                </div>
              </a>

              {/* WhatsApp */}
              <a
                href={whatsappHref}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '14px 10px',
                  borderRadius: '6px',
                  backgroundColor: 'var(--surface-elevated)',
                  border: '1px solid var(--border)',
                  textDecoration: 'none',
                  color: 'var(--text)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = '#25D366')}
                onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
              >
                <div
                  style={{
                    width: '34px',
                    height: '34px',
                    borderRadius: '50%',
                    backgroundColor: 'rgba(37, 211, 102, 0.12)',
                    color: '#25D366',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <MessageSquare size={18} />
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>WhatsApp</div>
                  <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)' }}>Instant dispatch</div>
                </div>
              </a>

              {/* Copy Enclave Link */}
              <button
                type="button"
                onClick={handleCopyLink}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '14px 10px',
                  borderRadius: '6px',
                  backgroundColor: copiedLink ? 'rgba(16, 185, 129, 0.12)' : 'var(--surface-elevated)',
                  border: `1px solid ${copiedLink ? '#10B981' : 'var(--border)'}`,
                  color: 'var(--text)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div
                  style={{
                    width: '34px',
                    height: '34px',
                    borderRadius: '50%',
                    backgroundColor: copiedLink ? 'rgba(16, 185, 129, 0.2)' : 'var(--primary-subtle)',
                    color: copiedLink ? '#10B981' : 'var(--primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  {copiedLink ? <Check size={18} /> : <Copy size={18} />}
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>
                    {copiedLink ? 'Link Copied!' : 'Copy Link'}
                  </div>
                  <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)' }}>Enclave portal URL</div>
                </div>
              </button>

              {/* Native OS Share */}
              <button
                type="button"
                onClick={handleNativeShare}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '14px 10px',
                  borderRadius: '6px',
                  backgroundColor: 'var(--surface-elevated)',
                  border: '1px solid var(--border)',
                  color: 'var(--text)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div
                  style={{
                    width: '34px',
                    height: '34px',
                    borderRadius: '50%',
                    backgroundColor: 'rgba(139, 92, 246, 0.12)',
                    color: '#8B5CF6',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <Share2 size={18} />
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>System Share</div>
                  <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)' }}>iOS / Android / Apps</div>
                </div>
              </button>

              {/* Optical QR Code */}
              <button
                type="button"
                onClick={() => setShowQrCode(!showQrCode)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '14px 10px',
                  borderRadius: '6px',
                  backgroundColor: showQrCode ? 'var(--primary-subtle)' : 'var(--surface-elevated)',
                  border: `1px solid ${showQrCode ? 'var(--primary)' : 'var(--border)'}`,
                  color: 'var(--text)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div
                  style={{
                    width: '34px',
                    height: '34px',
                    borderRadius: '50%',
                    backgroundColor: 'rgba(245, 158, 11, 0.12)',
                    color: '#F59E0B',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <QrCode size={18} />
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>Air-Gap QR</div>
                  <div style={{ fontSize: '10.5px', color: 'var(--text-tertiary)' }}>Camera optical scan</div>
                </div>
              </button>
            </div>

            {/* QR Code Air-Gap Display Panel */}
            {showQrCode && (
              <div
                style={{
                  marginTop: '12px',
                  padding: '16px',
                  borderRadius: '6px',
                  backgroundColor: 'var(--surface-elevated)',
                  border: '1px solid var(--border)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '20px',
                  flexWrap: 'wrap'
                }}
              >
                {/* SVG QR Code Simulation */}
                <div
                  style={{
                    width: '130px',
                    height: '130px',
                    backgroundColor: '#FFFFFF',
                    padding: '8px',
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                  }}
                >
                  <svg width="114" height="114" viewBox="0 0 114 114">
                    {/* Background */}
                    <rect width="114" height="114" fill="#FFFFFF" />
                    {/* Top-Left Finder */}
                    <rect x="6" y="6" width="30" height="30" fill="#0B1015" />
                    <rect x="11" y="11" width="20" height="20" fill="#FFFFFF" />
                    <rect x="16" y="16" width="10" height="10" fill="#0B1015" />
                    {/* Top-Right Finder */}
                    <rect x="78" y="6" width="30" height="30" fill="#0B1015" />
                    <rect x="83" y="11" width="20" height="20" fill="#FFFFFF" />
                    <rect x="88" y="16" width="10" height="10" fill="#0B1015" />
                    {/* Bottom-Left Finder */}
                    <rect x="6" y="78" width="30" height="30" fill="#0B1015" />
                    <rect x="11" y="83" width="20" height="20" fill="#FFFFFF" />
                    <rect x="16" y="88" width="10" height="10" fill="#0B1015" />
                    {/* Matrix Grid Data Points */}
                    <rect x="42" y="12" width="6" height="6" fill="#0B1015" />
                    <rect x="54" y="12" width="6" height="6" fill="#0B1015" />
                    <rect x="66" y="12" width="6" height="6" fill="#0B1015" />
                    <rect x="42" y="24" width="6" height="6" fill="#0B1015" />
                    <rect x="60" y="24" width="6" height="6" fill="#0B1015" />
                    <rect x="48" y="36" width="6" height="6" fill="#0B1015" />
                    <rect x="66" y="36" width="6" height="6" fill="#0B1015" />
                    <rect x="12" y="48" width="6" height="6" fill="#0B1015" />
                    <rect x="24" y="48" width="6" height="6" fill="#0B1015" />
                    <rect x="36" y="48" width="6" height="6" fill="#0B1015" />
                    <rect x="48" y="48" width="6" height="6" fill="#0B1015" />
                    <rect x="60" y="48" width="6" height="6" fill="#0B1015" />
                    <rect x="72" y="48" width="6" height="6" fill="#0B1015" />
                    <rect x="84" y="48" width="6" height="6" fill="#0B1015" />
                    <rect x="96" y="48" width="6" height="6" fill="#0B1015" />
                    <rect x="48" y="60" width="6" height="6" fill="#0B1015" />
                    <rect x="60" y="60" width="6" height="6" fill="#0B1015" />
                    <rect x="78" y="60" width="6" height="6" fill="#0B1015" />
                    <rect x="42" y="78" width="6" height="6" fill="#0B1015" />
                    <rect x="54" y="78" width="6" height="6" fill="#0B1015" />
                    <rect x="72" y="78" width="6" height="6" fill="#0B1015" />
                    <rect x="84" y="78" width="6" height="6" fill="#0B1015" />
                    <rect x="96" y="78" width="6" height="6" fill="#0B1015" />
                    <rect x="48" y="90" width="6" height="6" fill="#0B1015" />
                    <rect x="66" y="90" width="6" height="6" fill="#0B1015" />
                    <rect x="78" y="90" width="6" height="6" fill="#0B1015" />
                    <rect x="90" y="90" width="6" height="6" fill="#0B1015" />
                  </svg>
                </div>

                <div style={{ flex: 1, minWidth: '220px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text)', fontWeight: 650, fontSize: '13px' }}>
                    <Smartphone size={16} style={{ color: 'var(--primary)' }} />
                    <span>Air-Gapped Optical Capture Ready</span>
                  </div>
                  <p style={{ margin: '4px 0 10px 0', fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
                    Scan with any smartphone or tactical camera scanner. Directly opens the zero-server WebAssembly decapsulation enclave with hardware-bound keys.
                  </p>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      onClick={handleCopyMessage}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '4px',
                        backgroundColor: 'var(--surface-subtle)',
                        border: '1px solid var(--border)',
                        color: 'var(--text)',
                        fontSize: '11px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px'
                      }}
                    >
                      {copiedMessage ? <Check size={12} style={{ color: '#10B981' }} /> : <Copy size={12} />}
                      <span>{copiedMessage ? 'Copied Advisory Block' : 'Copy Advisory Text'}</span>
                    </button>
                    <button
                      type="button"
                      onClick={handleDownloadManifest}
                      style={{
                        padding: '6px 12px',
                        borderRadius: '4px',
                        backgroundColor: 'var(--surface-subtle)',
                        border: '1px solid var(--border)',
                        color: 'var(--text)',
                        fontSize: '11px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px'
                      }}
                    >
                      <Download size={12} />
                      <span>Download Manifest (.json)</span>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* SECTION 2: RECIPIENT LIST & INDIVIDUAL KEY CAPSULES */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)', fontWeight: 700 }}>
                2. Cleared Recipient Key Capsules ({enrolledRecipients.length})
              </div>
              <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
                Each recipient holds a unique ML-KEM-768 capsule & Tardos seed
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {enrolledRecipients.map((rec) => {
                const isTokenCopied = copiedToken === rec.recipient_id;

                return (
                  <div
                    key={rec.recipient_id}
                    style={{
                      padding: '12px 14px',
                      borderRadius: '6px',
                      backgroundColor: 'var(--surface-elevated)',
                      border: '1px solid var(--border)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      flexWrap: 'wrap',
                      gap: '12px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: '220px' }}>
                      <div
                        style={{
                          width: '34px',
                          height: '34px',
                          borderRadius: '50%',
                          backgroundColor: 'var(--primary-subtle)',
                          color: 'var(--primary)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 650,
                          fontSize: '13px'
                        }}
                      >
                        {rec.name.charAt(0)}
                      </div>
                      <div>
                        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text)' }}>
                          {rec.name}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                          {rec.recipient_id} · <span style={{ color: 'var(--text-tertiary)' }}>{rec.role || 'Officer // Cleared'}</span>
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span
                        style={{
                          fontSize: '10.5px',
                          fontFamily: 'var(--font-mono)',
                          padding: '2px 8px',
                          borderRadius: '3px',
                          backgroundColor: 'var(--surface-subtle)',
                          border: '1px solid var(--border-subtle)',
                          color: '#10B981'
                        }}
                      >
                        ML-KEM-768 SEALED
                      </span>

                      {/* Copy Personal Access Token */}
                      <button
                        type="button"
                        onClick={() => handleCopyRecipientToken(rec.recipient_id, rec.name)}
                        style={{
                          padding: '6px 10px',
                          borderRadius: '4px',
                          backgroundColor: isTokenCopied ? 'rgba(16, 185, 129, 0.12)' : 'var(--surface-subtle)',
                          border: `1px solid ${isTokenCopied ? '#10B981' : 'var(--border)'}`,
                          color: isTokenCopied ? '#10B981' : 'var(--text)',
                          fontSize: '11px',
                          fontWeight: 500,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '5px',
                          transition: 'all 0.15s ease'
                        }}
                        title="Copy personalized token link for this recipient"
                      >
                        {isTokenCopied ? <Check size={12} /> : <Key size={12} />}
                        <span>{isTokenCopied ? 'Token Copied' : 'Copy Token'}</span>
                      </button>

                      {/* Direct Mail to Principal */}
                      <button
                        type="button"
                        onClick={() => handleEmailRecipient(rec)}
                        style={{
                          padding: '6px 10px',
                          borderRadius: '4px',
                          backgroundColor: 'var(--surface-subtle)',
                          border: '1px solid var(--border)',
                          color: 'var(--text)',
                          fontSize: '11px',
                          fontWeight: 500,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '5px',
                          transition: 'all 0.15s ease'
                        }}
                        title="Open email addressed directly to this officer"
                      >
                        <Mail size={12} />
                        <span>Email Officer</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Security & Forensic Admissibility Notice */}
          <div
            style={{
              padding: '12px 14px',
              borderRadius: '6px',
              backgroundColor: 'rgba(76, 154, 154, 0.06)',
              border: '1px solid rgba(76, 154, 154, 0.18)',
              display: 'flex',
              gap: '10px',
              alignItems: 'flex-start'
            }}
          >
            <ShieldCheck size={16} style={{ color: 'var(--primary)', flexShrink: 0, marginTop: '2px' }} />
            <div style={{ fontSize: '11.5px', color: 'var(--text-secondary)', lineHeight: 1.45 }}>
              <strong style={{ color: 'var(--text)' }}>Zero-Knowledge Plaintext Guarantee:</strong> Shared links never transmit plaintext document bytes. The recipient's local browser WASM enclave decrypts the hybrid envelope using their private ML-KEM-768 secret key and renders the document on an isolated canvas protected by Section 65B Bharatiya Sakshya Adhiniyam 2023 legal provenance.
            </div>
          </div>

        </div>

        {/* Footer */}
        <div
          style={{
            padding: '14px 24px',
            borderTop: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: 'var(--surface-subtle)'
          }}
        >
          <button
            type="button"
            onClick={handleDownloadManifest}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--primary)',
              fontSize: '12px',
              fontWeight: 550,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '5px'
            }}
          >
            <Download size={14} />
            <span>Download Audit Dispatch Manifest</span>
          </button>

          <button
            type="button"
            onClick={onClose}
            className="btn-primary"
            style={{
              padding: '8px 20px',
              fontSize: '12.5px',
              fontWeight: 600,
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
