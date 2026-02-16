export const mouthMovement = {
  getScaleY(time, speaking) {
    if (!speaking) {
      return 0.2;
    }
    return 0.2 + (Math.sin(time * 18) * 0.5 + 0.5) * 0.55;
  },

  apply(mouthRef, time, speaking) {
    if (!mouthRef?.current) {
      return;
    }
    const scaleY = this.getScaleY(time, speaking);
    mouthRef.current.scale.y = scaleY;
  },
};

export const eyeBlinking = {
  getBlinkScaleY(time) {
    const cycle = Math.sin(time * 1.8) > 0.985;
    return cycle ? 0.08 : 1;
  },

  apply(leftEyeRef, rightEyeRef, time) {
    const scaleY = this.getBlinkScaleY(time);
    if (leftEyeRef?.current) {
      leftEyeRef.current.scale.y = scaleY;
    }
    if (rightEyeRef?.current) {
      rightEyeRef.current.scale.y = scaleY;
    }
  },
};

export const floatingEffect = {
  getOffset(time) {
    return Math.sin(time * 1.3) * 0.14;
  },

  apply(groupRef, time) {
    if (!groupRef?.current) {
      return;
    }
    groupRef.current.position.y = this.getOffset(time);
  },
};

export const glowingPulse = {
  getIntensity(time, speaking) {
    const base = speaking ? 1.25 : 0.8;
    const wave = speaking ? Math.sin(time * 7.5) : Math.sin(time * 2.5);
    return base + (wave * 0.5 + 0.5) * (speaking ? 0.8 : 0.35);
  },

  apply(materialRef, time, speaking) {
    if (!materialRef?.current) {
      return;
    }
    materialRef.current.emissiveIntensity = this.getIntensity(time, speaking);
  },
};

export const ringRotation = {
  getSpeed(index = 0) {
    return 0.18 + index * 0.07;
  },

  apply(ringRefs, time) {
    ringRefs.forEach((ringRef, index) => {
      if (!ringRef?.current) {
        return;
      }
      const speed = this.getSpeed(index);
      ringRef.current.rotation.x = time * speed * 0.7;
      ringRef.current.rotation.y = time * speed * (index % 2 === 0 ? 1 : -1);
      ringRef.current.rotation.z = time * speed * 0.5;
    });
  },
};

const avatarAnimations = {
  mouthMovement,
  eyeBlinking,
  floatingEffect,
  glowingPulse,
  ringRotation,
};

export default avatarAnimations;
