import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface ThreeSpectralCarrierProps {
  height?: number;
  recipientName?: string;
}

export const ThreeSpectralCarrier: React.FC<ThreeSpectralCarrierProps> = ({
  height = 250,
  recipientName = 'Marcus Vance'
}) => {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 500;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 14, 18);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // 1. Grid of 2D DCT Frequency Coefficients
    const gridRes = 24;
    const planeGeo = new THREE.PlaneGeometry(14, 14, gridRes, gridRes);
    planeGeo.rotateX(-Math.PI / 2);

    const pos = planeGeo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i);
      const z = pos.getZ(i);
      // Tardos pseudorandom orthogonal carrier modulation
      const dist = Math.sqrt(x * x + z * z);
      const wave1 = Math.sin(x * 1.2) * Math.cos(z * 1.2) * 1.2;
      const wave2 = Math.sin(dist * 2.0 - 0.5) * 0.8;
      const carrierNoise = ((i % 5) - 2) * 0.15;
      pos.setY(i, wave1 + wave2 + carrierNoise);
    }
    planeGeo.computeVertexNormals();

    // Wireframe carrier material
    const carrierMat = new THREE.MeshBasicMaterial({
      color: 0xF59E0B, // Amber carrier
      wireframe: true,
      transparent: true,
      opacity: 0.65
    });

    const carrierMesh = new THREE.Mesh(planeGeo, carrierMat);
    scene.add(carrierMesh);

    // Subtle coordinate plane
    const gridHelper = new THREE.GridHelper(16, 16, 0x38BDF8, 0x1E293B);
    gridHelper.position.y = -1.2;
    scene.add(gridHelper);

    // Mouse drag to rotate
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;
      carrierMesh.rotation.y += deltaX * 0.01;
      gridHelper.rotation.y += deltaX * 0.01;
      camera.position.y = Math.max(4, Math.min(26, camera.position.y - deltaY * 0.05));
      camera.lookAt(0, 0, 0);
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    // Handle Resize
    const handleResize = () => {
      if (!container) return;
      const newWidth = container.clientWidth;
      camera.aspect = newWidth / height;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, height);
    };
    window.addEventListener('resize', handleResize);

    // Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      if (!isDragging) {
        carrierMesh.rotation.y += 0.004;
        gridHelper.rotation.y += 0.004;
      }

      // Dynamic subtle pulsation of watermark frequencies
      const p = planeGeo.attributes.position;
      for (let i = 0; i < p.count; i++) {
        const x = p.getX(i);
        const z = p.getZ(i);
        const base = Math.sin(x * 1.2 + elapsedTime * 0.8) * Math.cos(z * 1.2 + elapsedTime * 0.8) * 1.1;
        p.setY(i, base);
      }
      p.needsUpdate = true;

      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      container.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      planeGeo.dispose();
      carrierMat.dispose();
      gridHelper.dispose();
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
        background: 'radial-gradient(ellipse at center, rgba(30, 20, 10, 0.4) 0%, rgba(9, 12, 15, 0.9) 100%)',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.4), inset 0 0 30px rgba(245, 158, 11, 0.05)'
      }}
    >
      <div ref={mountRef} style={{ width: '100%', height: '100%', cursor: 'grab' }} />

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
          border: '1px solid rgba(245, 158, 11, 0.25)'
        }}
      >
        <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--main-amber)', boxShadow: '0 0 8px var(--main-amber)' }} />
        <span style={{ fontSize: '11px', fontWeight: 600, color: '#FDE68A', letterSpacing: '0.04em' }}>
          3D SPECTRAL DSSS CARRIER · DRAG TO ROTATE
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
        2D DCT High-Frequency Domain · Orthogonal Tardos Codeword (U_bob)
      </div>
    </div>
  );
};
