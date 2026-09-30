import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { useTheme } from '../../context/ThemeContext';

interface Forensic3DBackgroundProps {
  interactive?: boolean;
  intensity?: number;
  className?: string;
  style?: React.CSSProperties;
}

export const Forensic3DBackground: React.FC<Forensic3DBackgroundProps> = ({
  interactive = true,
  intensity = 1.0,
  className = '',
  style
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();
  const isLight = theme === 'light';

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Check WebGL availability
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) return;
    } catch {
      return;
    }

    // 1. Scene & Camera Setup
    const scene = new THREE.Scene();
    
    // Atmospheric Fog
    const fogColor = isLight ? 0xF1F5F9 : 0x080C10;
    scene.fog = new THREE.FogExp2(fogColor, 0.0018);

    const camera = new THREE.PerspectiveCamera(
      55,
      window.innerWidth / window.innerHeight,
      1,
      2000
    );
    camera.position.z = 850;
    camera.position.y = 120;

    // 2. WebGL Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(fogColor, 0);
    container.appendChild(renderer.domElement);

    // 3. Cryptographic Color Palette
    const palette = {
      primary: isLight ? 0x0284C7 : 0x38BDF8,     // Petrol / Cyan
      secondary: isLight ? 0x0D9488 : 0x2DD4BF,   // Teal
      accent: isLight ? 0xD97706 : 0xF59E0B,      // Amber / Gold
      lattice: isLight ? 0x64748B : 0x1E293B,     // Deep Lattice Frame
      wire: isLight ? 0xCBD5E1 : 0x1A222D,        // Wave Terrain Wire
      particle: isLight ? 0x0284C7 : 0x67E8F9     // Quantum Dots
    };

    // 4. Central Post-Quantum LWE Lattice Geometry (Nested Polyhedral Cluster)
    const latticeGroup = new THREE.Group();
    scene.add(latticeGroup);

    // Outer Icosahedron Lattice
    const icoGeo = new THREE.IcosahedronGeometry(180, 1);
    const icoMat = new THREE.MeshBasicMaterial({
      color: palette.primary,
      wireframe: true,
      transparent: true,
      opacity: isLight ? 0.35 : 0.45
    });
    const icoMesh = new THREE.Mesh(icoGeo, icoMat);
    latticeGroup.add(icoMesh);

    // Inner Dodecahedron Core (Secret Key Space)
    const dodecaGeo = new THREE.DodecahedronGeometry(110, 0);
    const dodecaMat = new THREE.MeshBasicMaterial({
      color: palette.accent,
      wireframe: true,
      transparent: true,
      opacity: isLight ? 0.30 : 0.40
    });
    const dodecaMesh = new THREE.Mesh(dodecaGeo, dodecaMat);
    latticeGroup.add(dodecaMesh);

    // Core Quantum Singularity Sphere
    const coreGeo = new THREE.SphereGeometry(45, 16, 16);
    const coreMat = new THREE.MeshBasicMaterial({
      color: palette.secondary,
      wireframe: true,
      transparent: true,
      opacity: isLight ? 0.25 : 0.35
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    latticeGroup.add(coreMesh);

    // Orbital Merkle Ring
    const ringGeo = new THREE.TorusGeometry(260, 1.5, 8, 80);
    const ringMat = new THREE.MeshBasicMaterial({
      color: palette.primary,
      transparent: true,
      opacity: isLight ? 0.20 : 0.30
    });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.rotation.x = Math.PI / 3;
    latticeGroup.add(ringMesh);

    // Secondary Perpendicular Orbit Ring
    const ringGeo2 = new THREE.TorusGeometry(310, 1.2, 8, 80);
    const ringMat2 = new THREE.MeshBasicMaterial({
      color: palette.accent,
      transparent: true,
      opacity: isLight ? 0.15 : 0.25
    });
    const ringMesh2 = new THREE.Mesh(ringGeo2, ringMat2);
    ringMesh2.rotation.y = Math.PI / 4;
    ringMesh2.rotation.x = -Math.PI / 6;
    latticeGroup.add(ringMesh2);

    // 5. Floating Quantum Traitor-Tracing Particles (Tardos Code Points)
    const particleCount = 450;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    const particleVelocities: { x: number; y: number; z: number }[] = [];

    const fieldRadius = 750;
    for (let i = 0; i < particleCount; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      const dist = Math.pow(Math.random(), 0.5) * fieldRadius + 80;

      const x = dist * Math.sin(phi) * Math.cos(theta);
      const y = dist * Math.sin(phi) * Math.sin(theta);
      const z = dist * Math.cos(phi);

      particlePositions[i * 3] = x;
      particlePositions[i * 3 + 1] = y;
      particlePositions[i * 3 + 2] = z;

      particleVelocities.push({
        x: (Math.random() - 0.5) * 0.4,
        y: (Math.random() - 0.5) * 0.4,
        z: (Math.random() - 0.5) * 0.4
      });
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));

    // Custom Particle Texture
    const createCircleTexture = () => {
      const c = document.createElement('canvas');
      c.width = 64;
      c.height = 64;
      const ctx = c.getContext('2d');
      if (ctx) {
        const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 30);
        gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
        gradient.addColorStop(0.3, 'rgba(103, 232, 249, 0.8)');
        gradient.addColorStop(0.7, 'rgba(56, 189, 248, 0.2)');
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 64, 64);
      }
      return new THREE.CanvasTexture(c);
    };

    const particleMat = new THREE.PointsMaterial({
      size: 14,
      map: createCircleTexture(),
      transparent: true,
      opacity: isLight ? 0.65 : 0.85,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });

    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // 6. Dynamic Crystalline Merkle Line Connections
    const maxConnections = 600;
    const linePositions = new Float32Array(maxConnections * 6);
    const lineGeo = new THREE.BufferGeometry();
    lineGeo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));

    const lineMat = new THREE.LineBasicMaterial({
      color: palette.secondary,
      transparent: true,
      opacity: isLight ? 0.15 : 0.22,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });

    const lineMesh = new THREE.LineSegments(lineGeo, lineMat);
    scene.add(lineMesh);

    // 7. Undulating DSSS Spatial Frequency Carrier Wave Terrain
    const terrainWidth = 2400;
    const terrainHeight = 2400;
    const terrainSegments = 45;
    const terrainGeo = new THREE.PlaneGeometry(terrainWidth, terrainHeight, terrainSegments, terrainSegments);
    terrainGeo.rotateX(-Math.PI / 2);
    terrainGeo.translate(0, -320, 0);

    const terrainMat = new THREE.MeshBasicMaterial({
      color: palette.wire,
      wireframe: true,
      transparent: true,
      opacity: isLight ? 0.25 : 0.35
    });

    const terrainMesh = new THREE.Mesh(terrainGeo, terrainMat);
    scene.add(terrainMesh);

    // Store original terrain positions for wave modulation
    const terrainPosAttr = terrainGeo.attributes.position;
    const originalTerrainY = new Float32Array(terrainPosAttr.count);
    for (let i = 0; i < terrainPosAttr.count; i++) {
      originalTerrainY[i] = terrainPosAttr.getY(i);
    }

    // 8. Mouse Interaction & Inertia Tracking
    let mouseX = 0;
    let mouseY = 0;
    let targetCameraX = 0;
    let targetCameraY = 120;
    let windowHalfX = window.innerWidth / 2;
    let windowHalfY = window.innerHeight / 2;

    const handleMouseMove = (event: MouseEvent) => {
      if (!interactive) return;
      mouseX = (event.clientX - windowHalfX) * 0.4;
      mouseY = (event.clientY - windowHalfY) * 0.4;
    };

    const handleTouchMove = (event: TouchEvent) => {
      if (!interactive || !event.touches[0]) return;
      mouseX = (event.touches[0].clientX - windowHalfX) * 0.3;
      mouseY = (event.touches[0].clientY - windowHalfY) * 0.3;
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('touchmove', handleTouchMove, { passive: true });

    // Handle Window Resize
    const handleResize = () => {
      windowHalfX = window.innerWidth / 2;
      windowHalfY = window.innerHeight / 2;
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', handleResize);

    // 9. Animation Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      const elapsedTime = clock.getElapsedTime();

      // Smooth camera interpolation
      targetCameraX = mouseX * 0.6;
      targetCameraY = 120 - (mouseY * 0.4);
      camera.position.x += (targetCameraX - camera.position.x) * 0.035;
      camera.position.y += (targetCameraY - camera.position.y) * 0.035;
      camera.lookAt(0, 20, 0);

      // Central Lattice Cluster Rotation & Breathing
      const rotSpeed = 0.003 * intensity;
      icoMesh.rotation.x += rotSpeed * 1.2;
      icoMesh.rotation.y += rotSpeed * 1.5;

      dodecaMesh.rotation.x -= rotSpeed * 1.4;
      dodecaMesh.rotation.z += rotSpeed * 1.1;

      coreMesh.rotation.y += rotSpeed * 2.0;

      ringMesh.rotation.z += rotSpeed * 0.8;
      ringMesh2.rotation.z -= rotSpeed * 0.9;

      // Subtle breathing scale pulse
      const pulse = 1 + Math.sin(elapsedTime * 1.2) * 0.035;
      latticeGroup.scale.set(pulse, pulse, pulse);

      // Particle Field Evolution & Boundary Reflection
      const posArray = particleGeo.attributes.position.array as Float32Array;
      for (let i = 0; i < particleCount; i++) {
        const idx = i * 3;
        posArray[idx] += particleVelocities[i].x * intensity;
        posArray[idx + 1] += particleVelocities[i].y * intensity;
        posArray[idx + 2] += particleVelocities[i].z * intensity;

        // Soft spherical boundary bounce
        const distSq = posArray[idx] ** 2 + posArray[idx + 1] ** 2 + posArray[idx + 2] ** 2;
        if (distSq > fieldRadius ** 2) {
          particleVelocities[i].x *= -1;
          particleVelocities[i].y *= -1;
          particleVelocities[i].z *= -1;
        }
      }
      particleGeo.attributes.position.needsUpdate = true;

      // Update Merkle Dynamic Line Connections
      let lineIdx = 0;
      const connectionDist = 110;
      const connectionDistSq = connectionDist * connectionDist;

      for (let i = 0; i < particleCount && lineIdx < maxConnections; i++) {
        const p1x = posArray[i * 3];
        const p1y = posArray[i * 3 + 1];
        const p1z = posArray[i * 3 + 2];

        // Sample nearby candidates (stride to keep FPS buttery smooth at 60fps)
        for (let j = i + 1; j < Math.min(i + 24, particleCount) && lineIdx < maxConnections; j++) {
          const p2x = posArray[j * 3];
          const p2y = posArray[j * 3 + 1];
          const p2z = posArray[j * 3 + 2];

          const dx = p1x - p2x;
          const dy = p1y - p2y;
          const dz = p1z - p2z;
          const distSq = dx * dx + dy * dy + dz * dz;

          if (distSq < connectionDistSq) {
            const lPos = linePositions;
            const lIdx = lineIdx * 6;
            lPos[lIdx] = p1x;
            lPos[lIdx + 1] = p1y;
            lPos[lIdx + 2] = p1z;
            lPos[lIdx + 3] = p2x;
            lPos[lIdx + 4] = p2y;
            lPos[lIdx + 5] = p2z;
            lineIdx++;
          }
        }
      }

      // Zero out remaining line slots
      for (let k = lineIdx * 6; k < maxConnections * 6; k++) {
        linePositions[k] = 0;
      }
      lineGeo.attributes.position.needsUpdate = true;

      // Sinusoidal Wave Modulation on DSSS Terrain
      const terrainAttr = terrainGeo.attributes.position;
      const t = elapsedTime * 0.8;
      for (let i = 0; i < terrainAttr.count; i++) {
        const vx = terrainAttr.getX(i);
        const vz = terrainAttr.getZ(i);
        const wave = Math.sin(vx * 0.006 + t) * Math.cos(vz * 0.006 + t) * 28 +
                     Math.sin(vx * 0.012 - t * 0.5) * 14;
        terrainAttr.setY(i, originalTerrainY[i] + wave);
      }
      terrainGeo.attributes.position.needsUpdate = true;

      // Render Scene
      renderer.render(scene, camera);
    };

    animate();

    // 10. Clean up on unmount
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('resize', handleResize);

      if (container && renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }

      // Dispose Three.js objects
      icoGeo.dispose();
      icoMat.dispose();
      dodecaGeo.dispose();
      dodecaMat.dispose();
      coreGeo.dispose();
      coreMat.dispose();
      ringGeo.dispose();
      ringMat.dispose();
      ringGeo2.dispose();
      ringMat2.dispose();
      particleGeo.dispose();
      particleMat.dispose();
      lineGeo.dispose();
      lineMat.dispose();
      terrainGeo.dispose();
      terrainMat.dispose();
      renderer.dispose();
    };
  }, [isLight, interactive, intensity]);

  return (
    <div
      ref={containerRef}
      className={`forensic-3d-background ${className}`}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        pointerEvents: 'none',
        zIndex: 0,
        ...style
      }}
      aria-hidden="true"
    />
  );
};
