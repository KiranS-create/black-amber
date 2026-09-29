import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface ThreeMerkleChainProps {
  height?: number;
  isTampered?: boolean;
}

export const ThreeMerkleChain: React.FC<ThreeMerkleChainProps> = ({
  height = 180,
  isTampered = false
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const isTamperedRef = useRef(isTampered);
  isTamperedRef.current = isTampered;

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 600;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 1000);
    camera.position.set(0, 4, 16);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const group = new THREE.Group();
    scene.add(group);

    // 4 Floating Merkle Blocks (Cubes)
    const blockCount = 4;
    const blockMeshes: THREE.Mesh[] = [];
    const blockSpacing = 3.6;
    const startX = -((blockCount - 1) * blockSpacing) / 2;

    const cubeGeo = new THREE.BoxGeometry(1.6, 1.6, 1.6);

    for (let i = 0; i < blockCount; i++) {
      const mat = new THREE.MeshBasicMaterial({
        color: 0x10B981,
        wireframe: true,
        transparent: true,
        opacity: 0.8
      });
      const mesh = new THREE.Mesh(cubeGeo, mat);
      mesh.position.x = startX + i * blockSpacing;
      group.add(mesh);
      blockMeshes.push(mesh);
    }

    // Interconnecting beam lines
    const lineMat = new THREE.LineBasicMaterial({
      color: 0x38BDF8,
      transparent: true,
      opacity: 0.6
    });

    const lineGeo = new THREE.BufferGeometry();
    const linePositions = new Float32Array((blockCount - 1) * 6);
    for (let i = 0; i < blockCount - 1; i++) {
      linePositions[i * 6] = blockMeshes[i].position.x;
      linePositions[i * 6 + 1] = 0;
      linePositions[i * 6 + 2] = 0;

      linePositions[i * 6 + 3] = blockMeshes[i + 1].position.x;
      linePositions[i * 6 + 4] = 0;
      linePositions[i * 6 + 5] = 0;
    }
    lineGeo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
    const lines = new THREE.LineSegments(lineGeo, lineMat);
    group.add(lines);

    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const time = clock.getElapsedTime();
      const tampered = isTamperedRef.current;

      blockMeshes.forEach((mesh, idx) => {
        mesh.position.y = Math.sin(time * 1.5 + idx * 0.8) * 0.25;

        if (tampered && idx === 1) {
          // Block #1 is tampered: pulse crimson, jitter
          (mesh.material as THREE.MeshBasicMaterial).color.setHex(0xEF4444);
          mesh.rotation.x += 0.04;
          mesh.rotation.y += 0.06;
          mesh.position.y += Math.sin(time * 8.0) * 0.1;
        } else {
          // Healthy block
          (mesh.material as THREE.MeshBasicMaterial).color.setHex(idx === 0 ? 0x38BDF8 : 0x10B981);
          mesh.rotation.x += 0.008;
          mesh.rotation.y += 0.012;
        }
      });

      // Update connecting beam colors
      if (tampered) {
        lineMat.color.setHex(0xEF4444);
        lineMat.opacity = 0.3;
      } else {
        lineMat.color.setHex(0x38BDF8);
        lineMat.opacity = 0.6;
      }

      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!container) return;
      const newWidth = container.clientWidth;
      camera.aspect = newWidth / height;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, height);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      cubeGeo.dispose();
      blockMeshes.forEach(m => (m.material as THREE.Material).dispose());
      lineGeo.dispose();
      lineMat.dispose();
      renderer.dispose();
    };
  }, [height]);

  return (
    <div 
      style={{ 
        position: 'relative', 
        width: '100%', 
        height: `${height}px`, 
        overflow: 'hidden',
        borderRadius: '10px',
        background: isTampered 
          ? 'radial-gradient(ellipse at center, rgba(50, 10, 10, 0.45) 0%, rgba(9, 12, 15, 0.9) 100%)' 
          : 'radial-gradient(ellipse at center, rgba(14, 27, 46, 0.45) 0%, rgba(9, 12, 15, 0.9) 100%)',
        border: `1px solid ${isTampered ? 'rgba(239, 68, 68, 0.35)' : 'rgba(56, 189, 248, 0.2)'}`,
        boxShadow: `0 8px 32px 0 rgba(0, 0, 0, 0.4), inset 0 0 30px ${isTampered ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.05)'}`,
        transition: 'all 0.3s ease'
      }}
    >
      <div ref={mountRef} style={{ width: '100%', height: '100%' }} />

      <div 
        style={{
          position: 'absolute',
          top: '10px',
          left: '14px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          pointerEvents: 'none',
          backdropFilter: 'blur(8px)',
          background: 'rgba(9, 12, 15, 0.65)',
          padding: '4px 10px',
          borderRadius: '20px',
          border: `1px solid ${isTampered ? 'rgba(239, 68, 68, 0.3)' : 'rgba(255, 255, 255, 0.08)'}`
        }}
      >
        <span 
          style={{ 
            width: '6px', 
            height: '6px', 
            borderRadius: '50%', 
            background: isTampered ? 'var(--main-crimson)' : 'var(--main-jade)', 
            boxShadow: `0 0 8px ${isTampered ? 'var(--main-crimson)' : 'var(--main-jade)'}` 
          }} 
        />
        <span style={{ fontSize: '11px', fontWeight: 600, color: isTampered ? '#FCA5A5' : 'var(--main-text-primary)', letterSpacing: '0.04em' }}>
          {isTampered ? '3D MERKLE TREE: BLOCK #1 TAMPERED' : '3D MERKLE HASH CHAIN: INTEGRITY VERIFIED'}
        </span>
      </div>

      <div 
        style={{
          position: 'absolute',
          bottom: '8px',
          right: '12px',
          fontSize: '10px',
          color: 'var(--main-text-tertiary)',
          pointerEvents: 'none',
          fontFamily: 'monospace'
        }}
      >
        Genesis → Release #1 → Decryption Receipt #2 → Decryption Receipt #3
      </div>
    </div>
  );
};
