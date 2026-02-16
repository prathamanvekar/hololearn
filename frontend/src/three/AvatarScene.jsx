import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";

function createSpherePoints(count = 380, radius = 2.9) {
  const points = new Float32Array(count * 3);

  for (let index = 0; index < count; index += 1) {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    const distance = radius * Math.cbrt(Math.random());

    points[index * 3] = distance * Math.sin(phi) * Math.cos(theta);
    points[index * 3 + 1] = distance * Math.sin(phi) * Math.sin(theta);
    points[index * 3 + 2] = distance * Math.cos(phi);
  }

  return points;
}

export default function AvatarScene({ count = 380, radius = 2.9 }) {
  const pointsRef = useRef(null);

  const positions = useMemo(
    () => createSpherePoints(count, radius),
    [count, radius],
  );

  useFrame((state) => {
    if (!pointsRef.current) {
      return;
    }
    const elapsed = state.clock.getElapsedTime();
    pointsRef.current.rotation.y = elapsed * 0.08;
    pointsRef.current.rotation.x = Math.sin(elapsed * 0.3) * 0.18;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={positions.length / 3}
          itemSize={3}
          array={positions}
        />
      </bufferGeometry>
      <pointsMaterial
        color="#67e8f9"
        size={0.035}
        sizeAttenuation
        transparent
        opacity={0.72}
        depthWrite={false}
      />
    </points>
  );
}
