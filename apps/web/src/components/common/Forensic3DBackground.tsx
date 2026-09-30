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
    
    // Atmospheric Fog:
    // In light mode, fog density MUST be very subtle (0.00035) so geometry at z=850 is not washed out.
    // In dark mode, fog density 0.0016 produces a sleek cryptographic vignette.
    const fogColor = isLight ? 0xF8FAFC : 0x080C10;
    scene.fog = new THREE.FogExp2(fogColor, isLight ? 0.00035 : 0.0016);

    const camera = new THREE.PerspectiveCamera(
      55,
      window.innerWidth / window.innerHeight,
      1,
      2500
    );
    camera.position.z = 850;
    camera.position.y = 100;

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

    // Blending Mode:
    // CRITICAL: NormalBlending in light mode prevents white additive washout against light surfaces.
    // AdditiveBlending in dark mode provides luminous neon cyber glow.
    const activeBlending = isLight ? THREE.NormalBlending : THREE.AdditiveBlending;

    // 3. Cryptographic High-Contrast Color Palette
    const palette = {
      primary: isLight ? 0x0284C7 : 0x38BDF8,     // Petrol / Cyan (Sky 600 / Sky 400)
      secondary: isLight ? 0x0F766E : 0x2DD4BF,   // Emerald-Teal (Teal 700 / Teal 400)
      accent: isLight ? 0xD97706 : 0xF59E0B,      // Warm Amber (Amber 600 / Amber 400)
      lattice: isLight ? 0x475569 : 0x1E293B,     // Structural Lattice (Slate 600 / Slate 800)
      wire: isLight ? 0x94A3B8 : 0x1A222D,        // Wave Terrain Wire (Slate 400 / Dark Slate)
      particle: isLight ? 0x0369A1 : 0x67E8F9,    // Quantum Dots (Sky 700 / Cyan 300)
      laser: isLight ? 0x0284C7 : 0x38BDF8        // Cursor Entanglement Lasers
    };

    // 4. Central Post-Quantum LWE Lattice Geometry (Nested Polyhedral Enclave)
    const latticeGroup = new THREE.Group();
    scene.add(latticeGroup);

    // Outer Icosahedron Lattice
    const icoGeo = new THREE.IcosahedronGeometry(180, 1);
    const icoMat = new THREE.MeshBasicMaterial({
      color: palette.primary,
      wireframe: true,
      transparent: true,
      opacity: isLight ? 0.55 : 0.45,
      blending: activeBlending
    });
    const icoMesh = new THREE.Mesh(icoGeo, icoMat);
    latticeGroup.add(icoMesh);

    // Inner Dodecahedron Core (Secret Key Cryptographic Space)
    const dodecaGeo = new THREE.DodecahedronGeometry(110, 0);
    const dodecaMat = new THREE.MeshBasicMaterial({
      color: palette.accent,
      wireframe: true,
      transparent: true,
      opacity: isLight ? 0.45 : 0.40,
      blending: activeBlending
    });
    const dodecaMesh = new THREE.Mesh(dodecaGeo, dodecaMat);
    latticeGroup.add(dodecaMesh);

    // Core Quantum Singularity Sphere
    const coreGeo = new THREE.SphereGeometry(45, 16, 16);
    const coreMat = new THREE.MeshBasicMaterial({
      color: palette.secondary,
      wireframe: true,
      transparent: true,
      opacity: isLight ? 0.40 : 0.35,
      blending: activeBlending
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    latticeGroup.add(coreMesh);

    // Primary Merkle Orbital Ring
    const ringGeo = new THREE.TorusGeometry(260, 1.8, 8, 80);
    const ringMat = new THREE.MeshBasicMaterial({
      color: palette.primary,
      transparent: true,
      opacity: isLight ? 0.40 : 0.30,
      blending: activeBlending
    });
    const ringMesh = new THREE.Mesh(ringGeo, ringMat);
    ringMesh.rotation.x = Math.PI / 3;
    latticeGroup.add(ringMesh);

    // Secondary Perpendicular Orbit Ring
    const ringGeo2 = new THREE.TorusGeometry(310, 1.4, 8, 80);
    const ringMat2 = new THREE.MeshBasicMaterial({
      color: palette.accent,
      transparent: true,
      opacity: isLight ? 0.30 : 0.25,
      blending: activeBlending
    });
    const ringMesh2 = new THREE.Mesh(ringGeo2, ringMat2);
    ringMesh2.rotation.y = Math.PI / 4;
    ringMesh2.rotation.x = -Math.PI / 6;
    latticeGroup.add(ringMesh2);

    // 5. Interactive Quantum Particles (Tardos Code Points & Mouse Attraction Swarm)
    const particleCount = 480;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    const homePositions = new Float32Array(particleCount * 3);
    const particleVelocities: { x: number; y: number; z: number }[] = [];

    const fieldRadius = 780;
    for (let i = 0; i < particleCount; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      const dist = Math.pow(Math.random(), 0.6) * fieldRadius + 70;

      const x = dist * Math.sin(phi) * Math.cos(theta);
      const y = dist * Math.sin(phi) * Math.sin(theta);
      const z = dist * Math.cos(phi);

      particlePositions[i * 3] = x;
      particlePositions[i * 3 + 1] = y;
      particlePositions[i * 3 + 2] = z;

      homePositions[i * 3] = x;
      homePositions[i * 3 + 1] = y;
      homePositions[i * 3 + 2] = z;

      particleVelocities.push({
        x: (Math.random() - 0.5) * 0.3,
        y: (Math.random() - 0.5) * 0.3,
        z: (Math.random() - 0.5) * 0.3
      });
    }

    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));

    // Custom Dynamic Particle Texture Generator:
    // In light mode: deep saturated center (#0284C7) + vibrant teal ring (#0F766E) so it pops crisp on white.
    // In dark mode: luminous white hot center + cyan aura.
    const createCircleTexture = () => {
      const c = document.createElement('canvas');
      c.width = 64;
      c.height = 64;
      const ctx = c.getContext('2d');
      if (ctx) {
        const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 30);
        if (isLight) {
          gradient.addColorStop(0, 'rgba(2, 132, 199, 1)');      // Rich saturated Sky-600
          gradient.addColorStop(0.35, 'rgba(15, 118, 110, 0.95)'); // Deep Teal-700
          gradient.addColorStop(0.70, 'rgba(56, 189, 248, 0.45)'); // Sky-400 aura
          gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
        } else {
          gradient.addColorStop(0, 'rgba(255, 255, 255, 1)');
          gradient.addColorStop(0.30, 'rgba(103, 232, 249, 0.9)');
          gradient.addColorStop(0.70, 'rgba(56, 189, 248, 0.3)');
          gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
        }
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 64, 64);
      }
      return new THREE.CanvasTexture(c);
    };

    const particleMat = new THREE.PointsMaterial({
      size: isLight ? 16 : 14,
      map: createCircleTexture(),
      transparent: true,
      opacity: isLight ? 0.90 : 0.85,
      blending: activeBlending,
      depthWrite: false
    });

    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // 6. Dynamic Crystalline Merkle Line Connections
    const maxConnections = 650;
    const linePositions = new Float32Array(maxConnections * 6);
    const lineGeo = new THREE.BufferGeometry();
    lineGeo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));

    const lineMat = new THREE.LineBasicMaterial({
      color: palette.secondary,
      transparent: true,
      opacity: isLight ? 0.38 : 0.22,
      blending: activeBlending,
      depthWrite: false
    });

    const lineMesh = new THREE.LineSegments(lineGeo, lineMat);
    scene.add(lineMesh);

    // 7. Dynamic Cursor Entanglement Laser Filaments (Connections from mouse to nearby particles)
    const maxLaserBeams = 12;
    const laserPositions = new Float32Array(maxLaserBeams * 6);
    const laserGeo = new THREE.BufferGeometry();
    laserGeo.setAttribute('position', new THREE.BufferAttribute(laserPositions, 3));

    const laserMat = new THREE.LineBasicMaterial({
      color: palette.laser,
      transparent: true,
      opacity: isLight ? 0.55 : 0.70,
      blending: activeBlending,
      depthWrite: false
    });

    const laserMesh = new THREE.LineSegments(laserGeo, laserMat);
    scene.add(laserMesh);

    // 8. 3D Holographic Magnetic Cursor Beacon Anchor
    const cursorBeaconGroup = new THREE.Group();
    scene.add(cursorBeaconGroup);

    const beaconRingGeo = new THREE.TorusGeometry(22, 1.2, 8, 36);
    const beaconRingMat = new THREE.MeshBasicMaterial({
      color: palette.primary,
      transparent: true,
      opacity: isLight ? 0.65 : 0.80,
      blending: activeBlending
    });
    const beaconRingMesh = new THREE.Mesh(beaconRingGeo, beaconRingMat);
    cursorBeaconGroup.add(beaconRingMesh);

    const beaconDotGeo = new THREE.SphereGeometry(3.5, 12, 12);
    const beaconDotMat = new THREE.MeshBasicMaterial({
      color: palette.accent,
      transparent: true,
      opacity: isLight ? 0.85 : 0.95,
      blending: activeBlending
    });
    const beaconDotMesh = new THREE.Mesh(beaconDotGeo, beaconDotMat);
    cursorBeaconGroup.add(beaconDotMesh);

    // 9. Undulating DSSS Spatial Frequency Carrier Wave Terrain
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
      opacity: isLight ? 0.35 : 0.35
    });

    const terrainMesh = new THREE.Mesh(terrainGeo, terrainMat);
    scene.add(terrainMesh);

    const terrainPosAttr = terrainGeo.attributes.position;
    const originalTerrainY = new Float32Array(terrainPosAttr.count);
    for (let i = 0; i < terrainPosAttr.count; i++) {
      originalTerrainY[i] = terrainPosAttr.getY(i);
    }

    // 10. Mouse Interaction, 3D Raycasting & Magnetic Targeting
    let mouseX = 0;
    let mouseY = 0;
    let targetCameraX = 0;
    let targetCameraY = 100;
    let windowHalfX = window.innerWidth / 2;
    let windowHalfY = window.innerHeight / 2;

    const mouseNDC = new THREE.Vector2(-999, -999);
    const raycaster = new THREE.Raycaster();
    const planeZ0 = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
    const mouseWorldTarget = new THREE.Vector3(0, 0, 0);
    const mouseCurrent3D = new THREE.Vector3(0, 0, 0);
    let isMouseInView = false;

    const handleMouseMove = (event: MouseEvent) => {
      if (!interactive) return;
      isMouseInView = true;
      mouseX = (event.clientX - windowHalfX) * 0.35;
      mouseY = (event.clientY - windowHalfY) * 0.35;

      mouseNDC.x = (event.clientX / window.innerWidth) * 2 - 1;
      mouseNDC.y = -(event.clientY / window.innerHeight) * 2 + 1;
    };

    const handleTouchMove = (event: TouchEvent) => {
      if (!interactive || !event.touches[0]) return;
      isMouseInView = true;
      const touch = event.touches[0];
      mouseX = (touch.clientX - windowHalfX) * 0.25;
      mouseY = (touch.clientY - windowHalfY) * 0.25;

      mouseNDC.x = (touch.clientX / window.innerWidth) * 2 - 1;
      mouseNDC.y = -(touch.clientY / window.innerHeight) * 2 + 1;
    };

    const handleMouseLeave = () => {
      isMouseInView = false;
      mouseNDC.set(-999, -999);
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('touchmove', handleTouchMove, { passive: true });
    document.addEventListener('mouseleave', handleMouseLeave);

    const handleResize = () => {
      windowHalfX = window.innerWidth / 2;
      windowHalfY = window.innerHeight / 2;
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', handleResize);

    // 11. Animation Loop & Physics Engine
    let animationFrameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      const elapsedTime = clock.getElapsedTime();

      // Smooth camera interpolation
      targetCameraX = mouseX * 0.5;
      targetCameraY = 100 - (mouseY * 0.35);
      camera.position.x += (targetCameraX - camera.position.x) * 0.04;
      camera.position.y += (targetCameraY - camera.position.y) * 0.04;
      camera.lookAt(0, 15, 0);

      // Unproject mouse coordinates into 3D world space on the z=0 plane
      if (isMouseInView && mouseNDC.x > -2) {
        raycaster.setFromCamera(mouseNDC, camera);
        raycaster.ray.intersectPlane(planeZ0, mouseWorldTarget);
        // Smoothly interpolate current 3D mouse vector
        mouseCurrent3D.lerp(mouseWorldTarget, 0.12);
        cursorBeaconGroup.position.copy(mouseCurrent3D);
        cursorBeaconGroup.visible = true;

        beaconRingMesh.rotation.z += 0.025;
        const beaconPulse = 1 + Math.sin(elapsedTime * 6) * 0.12;
        beaconRingMesh.scale.set(beaconPulse, beaconPulse, beaconPulse);
      } else {
        cursorBeaconGroup.visible = false;
      }

      // Central Lattice Cluster Rotation & Subtle Tilt toward cursor
      const rotSpeed = 0.003 * intensity;
      icoMesh.rotation.x += rotSpeed * 1.2;
      icoMesh.rotation.y += rotSpeed * 1.5;

      dodecaMesh.rotation.x -= rotSpeed * 1.4;
      dodecaMesh.rotation.z += rotSpeed * 1.1;

      coreMesh.rotation.y += rotSpeed * 2.0;

      ringMesh.rotation.z += rotSpeed * 0.8;
      ringMesh2.rotation.z -= rotSpeed * 0.9;

      const pulse = 1 + Math.sin(elapsedTime * 1.2) * 0.035;
      latticeGroup.scale.set(pulse, pulse, pulse);

      // Magnetic Attraction & Swarming Vortex Physics
      const posArray = particleGeo.attributes.position.array as Float32Array;
      const attractionRadius = 380;
      const attractionRadiusSq = attractionRadius * attractionRadius;

      // Track closest particles to cursor for laser filaments
      const nearbyParticles: { index: number; distSq: number }[] = [];

      for (let i = 0; i < particleCount; i++) {
        const idx = i * 3;
        let px = posArray[idx];
        let py = posArray[idx + 1];
        let pz = posArray[idx + 2];

        // Celestial slow drift of home position
        const angle = rotSpeed * 0.15;
        const hx = homePositions[idx];
        const hy = homePositions[idx + 1];
        const hz = homePositions[idx + 2];
        homePositions[idx] = hx * Math.cos(angle) - hz * Math.sin(angle);
        homePositions[idx + 2] = hx * Math.sin(angle) + hz * Math.cos(angle);

        // Magnetic Attraction towards Mouse Pointer
        if (isMouseInView) {
          const dx = mouseCurrent3D.x - px;
          const dy = mouseCurrent3D.y - py;
          const dz = mouseCurrent3D.z - pz;
          const distSq = dx * dx + dy * dy + dz * dz;

          if (distSq < attractionRadiusSq) {
            const dist = Math.sqrt(distSq);

            // Record for laser filament rendering
            if (dist < 280) {
              nearbyParticles.push({ index: i, distSq });
            }

            if (dist > 18) {
              const unitX = dx / dist;
              const unitY = dy / dist;
              const unitZ = dz / dist;

              // Pull force increases quadratically as cursor approaches
              const pullFactor = Math.pow(1 - dist / attractionRadius, 1.4) * 3.4 * intensity;
              particleVelocities[i].x += unitX * pullFactor;
              particleVelocities[i].y += unitY * pullFactor;
              particleVelocities[i].z += unitZ * pullFactor;

              // Tangential Swirl Force (Creates an orbiting quantum vortex around the cursor)
              const swirlFactor = pullFactor * 1.35;
              particleVelocities[i].x += -unitY * swirlFactor;
              particleVelocities[i].y += unitX * swirlFactor;
            } else {
              // Gentle core repulsion so particles swirl in an orbit rather than collapsing into a dot
              particleVelocities[i].x -= (dx / 18) * 1.2;
              particleVelocities[i].y -= (dy / 18) * 1.2;
            }
          }
        }

        // Hooke's Spring Restoration Force towards Home Position
        const hdx = homePositions[idx] - px;
        const hdy = homePositions[idx + 1] - py;
        const hdz = homePositions[idx + 2] - pz;
        particleVelocities[i].x += hdx * 0.016;
        particleVelocities[i].y += hdy * 0.016;
        particleVelocities[i].z += hdz * 0.016;

        // Velocity Damping (Organic liquid viscosity)
        particleVelocities[i].x *= 0.92;
        particleVelocities[i].y *= 0.92;
        particleVelocities[i].z *= 0.92;

        // Position Integration
        px += particleVelocities[i].x * intensity;
        py += particleVelocities[i].y * intensity;
        pz += particleVelocities[i].z * intensity;

        posArray[idx] = px;
        posArray[idx + 1] = py;
        posArray[idx + 2] = pz;
      }
      particleGeo.attributes.position.needsUpdate = true;

      // Update Laser Entanglement Filaments
      nearbyParticles.sort((a, b) => a.distSq - b.distSq);
      const activeLasers = Math.min(nearbyParticles.length, maxLaserBeams);
      let laserIdx = 0;

      if (isMouseInView && activeLasers > 0) {
        for (let l = 0; l < activeLasers; l++) {
          const pIdx = nearbyParticles[l].index * 3;
          const beamOffset = laserIdx * 6;

          laserPositions[beamOffset] = mouseCurrent3D.x;
          laserPositions[beamOffset + 1] = mouseCurrent3D.y;
          laserPositions[beamOffset + 2] = mouseCurrent3D.z;

          laserPositions[beamOffset + 3] = posArray[pIdx];
          laserPositions[beamOffset + 4] = posArray[pIdx + 1];
          laserPositions[beamOffset + 5] = posArray[pIdx + 2];
          laserIdx++;
        }
      }

      // Clear remaining laser segments
      for (let k = laserIdx * 6; k < maxLaserBeams * 6; k++) {
        laserPositions[k] = 0;
      }
      laserGeo.attributes.position.needsUpdate = true;

      // Update Merkle Dynamic Line Connections between particles
      let lineIdx = 0;
      const connectionDist = 115;
      const connectionDistSq = connectionDist * connectionDist;

      for (let i = 0; i < particleCount && lineIdx < maxConnections; i++) {
        const p1x = posArray[i * 3];
        const p1y = posArray[i * 3 + 1];
        const p1z = posArray[i * 3 + 2];

        for (let j = i + 1; j < Math.min(i + 24, particleCount) && lineIdx < maxConnections; j++) {
          const p2x = posArray[j * 3];
          const p2y = posArray[j * 3 + 1];
          const p2z = posArray[j * 3 + 2];

          const dx = p1x - p2x;
          const dy = p1y - p2y;
          const dz = p1z - p2z;
          const distSq = dx * dx + dy * dy + dz * dz;

          if (distSq < connectionDistSq) {
            const lIdx = lineIdx * 6;
            linePositions[lIdx] = p1x;
            linePositions[lIdx + 1] = p1y;
            linePositions[lIdx + 2] = p1z;
            linePositions[lIdx + 3] = p2x;
            linePositions[lIdx + 4] = p2y;
            linePositions[lIdx + 5] = p2z;
            lineIdx++;
          }
        }
      }

      for (let k = lineIdx * 6; k < maxConnections * 6; k++) {
        linePositions[k] = 0;
      }
      lineGeo.attributes.position.needsUpdate = true;

      // Sinusoidal Wave Modulation on Carrier Wave Terrain
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

    // 12. Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      window.removeEventListener('resize', handleResize);

      if (container && renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }

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
      beaconRingGeo.dispose();
      beaconRingMat.dispose();
      beaconDotGeo.dispose();
      beaconDotMat.dispose();
      particleGeo.dispose();
      particleMat.dispose();
      lineGeo.dispose();
      lineMat.dispose();
      laserGeo.dispose();
      laserMat.dispose();
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
