import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface ThreeCryptographicLatticeProps {
  height?: number;
  interactive?: boolean;
}

export const ThreeCryptographicLattice: React.FC<ThreeCryptographicLatticeProps> = ({
  height = 220,
  interactive = true
}) => {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 600;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 24;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // 1. Group for entire lattice
    const latticeGroup = new THREE.Group();
    scene.add(latticeGroup);

    // 2. Central PQC Polyhedron Core (Icosahedron wireframe)
    const coreGeo = new THREE.IcosahedronGeometry(4.2, 1);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x38BDF8,
      wireframe: true,
      transparent: true,
      opacity: 0.35
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    latticeGroup.add(coreMesh);

    // 3. Inner dense Merkle Node Core
    const innerGeo = new THREE.OctahedronGeometry(2.4, 0);
    const innerMat = new THREE.MeshBasicMaterial({
      color: 0x10B981,
      wireframe: true,
      transparent: true,
      opacity: 0.6
    });
    const innerMesh = new THREE.Mesh(innerGeo, innerMat);
    latticeGroup.add(innerMesh);

    // 4. Floating lattice particle cloud (ML-KEM-768 coefficient vectors)
    const particleCount = 120;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const color1 = new THREE.Color(0x38BDF8); // Cyan
    const color2 = new THREE.Color(0x10B981); // Emerald
    const color3 = new THREE.Color(0xF59E0B); // Amber

    for (let i = 0; i < particleCount; i++) {
      const radius = 5.5 + Math.random() * 6.5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);

      const chosenColor = i % 3 === 0 ? color1 : i % 3 === 1 ? color2 : color3;
      colors[i * 3] = chosenColor.r;
      colors[i * 3 + 1] = chosenColor.g;
      colors[i * 3 + 2] = chosenColor.b;
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const particleMat = new THREE.PointsMaterial({
      size: 0.28,
      vertexColors: true,
      transparent: true,
      opacity: 0.85
    });

    const particles = new THREE.Points(particleGeo, particleMat);
    latticeGroup.add(particles);

    // 5. Interconnecting Laser Filaments (Merkle Tree Links)
    const lineIndices: number[] = [];
    for (let i = 0; i < particleCount; i++) {
      for (let j = i + 1; j < particleCount; j++) {
        const dx = positions[i * 3] - positions[j * 3];
        const dy = positions[i * 3 + 1] - positions[j * 3 + 1];
        const dz = positions[i * 3 + 2] - positions[j * 3 + 2];
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (dist < 3.2) {
          lineIndices.push(i, j);
        }
      }
    }

    const lineGeo = new THREE.BufferGeometry();
    lineGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    lineGeo.setIndex(lineIndices);

    const lineMat = new THREE.LineBasicMaterial({
      color: 0x38BDF8,
      transparent: true,
      opacity: 0.15
    });

    const lines = new THREE.LineSegments(lineGeo, lineMat);
    latticeGroup.add(lines);

    // Mouse Parallax Interaction
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      if (!interactive) return;
      const rect = container.getBoundingClientRect();
      mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
    };

    container.addEventListener('mousemove', handleMouseMove);

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
    const animate = () => {
      animId = requestAnimationFrame(animate);

      // Smooth mouse follow
      targetX += (mouseX * 0.4 - targetX) * 0.05;
      targetY += (mouseY * 0.4 - targetY) * 0.05;

      latticeGroup.rotation.y += 0.003 + targetX * 0.02;
      latticeGroup.rotation.x += 0.002 + targetY * 0.02;
      innerMesh.rotation.y -= 0.006;
      innerMesh.rotation.z += 0.004;

      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      container.removeEventListener('mousemove', handleMouseMove);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      coreGeo.dispose();
      coreMat.dispose();
      innerGeo.dispose();
      innerMat.dispose();
      particleGeo.dispose();
      particleMat.dispose();
      lineGeo.dispose();
      lineMat.dispose();
      renderer.dispose();
    };
  }, [height, interactive]);

  return (
    <div 
      style={{ 
        position: 'relative', 
        width: '100%', 
        height: `${height}px`, 
        overflow: 'hidden',
        borderRadius: '12px',
        background: 'radial-gradient(ellipse at center, rgba(14, 27, 46, 0.45) 0%, rgba(9, 12, 15, 0.85) 100%)',
        border: '1px solid rgba(56, 189, 248, 0.2)',
        boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.4), inset 0 0 40px rgba(56, 189, 248, 0.05)'
      }}
    >
      {/* Three.js Canvas Container */}
      <div ref={mountRef} style={{ width: '100%', height: '100%', cursor: 'grab' }} />

      {/* Glassmorphic Overlay HUD */}
      <div 
        style={{
          position: 'absolute',
          top: '12px',
          left: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          pointerEvents: 'none',
          backdropFilter: 'blur(8px)',
          background: 'rgba(9, 12, 15, 0.6)',
          padding: '4px 10px',
          borderRadius: '20px',
          border: '1px solid rgba(255, 255, 255, 0.08)'
        }}
      >
        <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--main-jade)', boxShadow: '0 0 8px var(--main-jade)' }} />
        <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--main-text-primary)', letterSpacing: '0.04em' }}>
          3D PQC LATTICE CORE · ML-KEM-768 / MERKLE DLT
        </span>
      </div>

      <div 
        style={{
          position: 'absolute',
          bottom: '10px',
          right: '16px',
          fontSize: '10px',
          color: 'var(--main-text-tertiary)',
          pointerEvents: 'none',
          fontFamily: 'monospace'
        }}
      >
        Ring-LWE q=3329 · k=3 · High-Dimensional Orthogonal Lattice
      </div>
    </div>
  );
};
