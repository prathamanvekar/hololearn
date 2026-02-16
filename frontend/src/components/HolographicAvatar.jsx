import {
  ContactShadows,
  Environment,
  Float,
  OrbitControls,
  useGLTF,
} from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { Component, Suspense, useMemo, useRef } from "react";
import * as THREE from "three";
import { Volume2, Waves } from "lucide-react";
import { useAppContext } from "../context/useAppContext";

const MODEL_PATH = "/models/avatar.glb";

class AvatarCanvasErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-full w-full flex items-center justify-center rounded-2xl border border-white/10 bg-slate-950/50">
          <p className="text-sm text-slate-300">Unable to load avatar model.</p>
        </div>
      );
    }
    return this.props.children;
  }
}

function LoadingFallback() {
  const wireRef = useRef(null);

  useFrame((state) => {
    if (!wireRef.current) {
      return;
    }
    wireRef.current.rotation.y = state.clock.getElapsedTime() * 0.8;
  });

  return (
    <group>
      <mesh ref={wireRef}>
        <sphereGeometry args={[0.9, 24, 24]} />
        <meshBasicMaterial color="#67e8f9" wireframe />
      </mesh>
      <ContactShadows
        position={[0, -1.4, 0]}
        opacity={0.4}
        scale={4}
        blur={1.8}
        far={2}
        color="#00d4ff"
      />
    </group>
  );
}

function Avatar3D({ speaking }) {
  const groupRef = useRef(null);
  const { scene } = useGLTF(MODEL_PATH);
  const model = useMemo(() => scene?.clone(true) ?? null, [scene]);
  const modelTransform = useMemo(() => {
    if (!model) {
      return {
        offsetX: 0,
        offsetY: -1.1,
        offsetZ: 0,
        scale: 1,
      };
    }

    const box = new THREE.Box3().setFromObject(model);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);

    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    const targetHeight = 2.45;
    const scale = targetHeight / maxDim;

    // Scale and vertical offset may need minor tweaking per GLB asset proportions.
    return {
      offsetX: -center.x,
      offsetY: -box.min.y,
      offsetZ: -center.z,
      scale: scale * 0.7,
    };
  }, [model]);

  useFrame((state) => {
    if (!groupRef.current) {
      return;
    }

    const t = state.clock.getElapsedTime();
    const floatAmp = speaking ? 0.12 : 0.07;
    const floatSpeed = speaking ? 2.3 : 1.4;
    const rotateSpeed = speaking ? 0.35 : 0.16;

    groupRef.current.position.y = Math.sin(t * floatSpeed) * floatAmp;
    groupRef.current.rotation.y += rotateSpeed * 0.003;
  });

  if (!model) {
    return <LoadingFallback />;
  }

  return (
    <Float
      speed={speaking ? 1.9 : 1.2}
      rotationIntensity={speaking ? 0.25 : 0.12}
      floatIntensity={0.2}
    >
      <group ref={groupRef} position={[0, -0.05, 0]}>
        <group
          position={[
            modelTransform.offsetX,
            modelTransform.offsetY,
            modelTransform.offsetZ,
          ]}
          scale={modelTransform.scale}
        >
          <primitive object={model} />
        </group>
      </group>
      <ContactShadows
        position={[0, -1.48, 0]}
        opacity={0.45}
        scale={5.2}
        blur={2.4}
        far={2.3}
        color="#00d4ff"
      />
    </Float>
  );
}

export default function HolographicAvatar() {
  const { avatar } = useAppContext();
  const avatarSpeaking = Boolean(avatar?.speaking);
  const avatarMessage =
    avatar?.message ||
    "Send a message in chat to make the holographic tutor respond.";

  return (
    <section className="glass-panel h-full min-h-105 p-4 md:p-5 flex flex-col gap-3 animate-fade-in">
      <header className="flex items-center justify-between gap-3 border-b border-white/10 pb-3">
        <div className="flex items-center gap-2.5">
          <div
            className={`h-9 w-9 rounded-xl border flex items-center justify-center ${avatarSpeaking ? "border-cyan-300/60 bg-cyan-400/15 hologram-glow" : "border-purple-300/40 bg-purple-500/10"}`}
          >
            <Waves
              size={17}
              className={avatarSpeaking ? "text-cyan-200" : "text-purple-200"}
            />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.14em] text-slate-400">
              3D Tutor
            </p>
            <h3 className="text-lg font-semibold hologram-text">
              Holographic Assistant
            </h3>
          </div>
        </div>

        <div
          className={`badge ${avatarSpeaking ? "badge-cyan animate-pulse" : "badge-purple"}`}
        >
          <Volume2 size={13} /> {avatarSpeaking ? "Speaking" : "Standby"}
        </div>
      </header>

      <div className="relative flex-1 min-h-80 rounded-2xl border border-white/10 overflow-hidden bg-slate-950/40">
        <AvatarCanvasErrorBoundary>
          <Canvas
            dpr={[1, 2]}
            camera={{ position: [0, 0.3, 4.1], fov: 36 }}
            gl={{ alpha: true, antialias: true }}
          >
            <ambientLight intensity={0.62} />
            <directionalLight
              position={[2.2, 3.1, 3.1]}
              intensity={1.35}
              color="#ffffff"
            />
            <pointLight
              position={[3, 1.7, 2]}
              intensity={0.95}
              color="#00d4ff"
            />
            <pointLight
              position={[-2.8, 1.2, -1.8]}
              intensity={0.88}
              color="#8b5cf6"
            />
            <Environment preset="city" />

            <Suspense fallback={<LoadingFallback />}>
              <Avatar3D speaking={avatarSpeaking} />
            </Suspense>

            <OrbitControls
              enableZoom={false}
              enablePan={false}
              enableDamping
              dampingFactor={0.08}
              minPolarAngle={Math.PI / 2.8}
              maxPolarAngle={Math.PI / 1.95}
            />
          </Canvas>
        </AvatarCanvasErrorBoundary>

        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-cyan-500/12 via-transparent to-purple-500/10" />
        <div className="pointer-events-none absolute left-0 right-0 bottom-0 h-20 bg-gradient-to-t from-slate-950/85 to-transparent" />
        <div className="pointer-events-none absolute left-0 right-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-300/65 to-transparent" />
        <div className="pointer-events-none absolute left-0 right-0 bottom-0 h-px bg-gradient-to-r from-transparent via-purple-300/65 to-transparent" />
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.08]"
          style={{
            backgroundImage:
              "repeating-linear-gradient(to bottom, rgba(255,255,255,0.22) 0px, rgba(255,255,255,0.22) 1px, transparent 1px, transparent 6px)",
          }}
        />
      </div>

      <footer className="card min-h-21 transition-colors duration-300">
        <p className="text-xs uppercase tracking-[0.12em] text-slate-400 mb-1">
          Current Avatar Message
        </p>
        <p
          className={`text-sm ${avatarSpeaking ? "text-cyan-100" : "text-slate-200"}`}
        >
          {avatarMessage}
        </p>
      </footer>
    </section>
  );
}

useGLTF.preload(MODEL_PATH);
