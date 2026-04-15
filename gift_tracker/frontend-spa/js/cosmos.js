const DPR_MAX = 2;
const NODE_DENSITY = 16500;
const BASE_LINK_DISTANCE = 132;
const POINTER_GRAVITY_RADIUS = 180;
const PALETTE = [
  [127, 116, 143],
  [144, 130, 161],
  [114, 104, 132],
  [160, 148, 173],
  [188, 193, 201],
];

function rand(min, max) {
  return Math.random() * (max - min) + min;
}

function pickTone(signal) {
  return PALETTE[Math.floor(signal * PALETTE.length) % PALETTE.length];
}

function buildNodes(count, width, height) {
  const nodes = [];
  for (let i = 0; i < count; i += 1) {
    const tier = Math.random();
    const luminosity = tier < 0.09 ? rand(0.82, 1) : tier < 0.34 ? rand(0.45, 0.78) : rand(0.18, 0.44);
    const radius = tier < 0.09 ? rand(1.45, 2.3) : tier < 0.34 ? rand(0.9, 1.45) : rand(0.5, 0.92);
    nodes.push({
      x: rand(0, width),
      y: rand(0, height),
      vx: rand(-0.12, 0.12),
      vy: rand(-0.12, 0.12),
      r: radius,
      signal: rand(0.08, 1),
      drift: rand(0.0015, 0.0042),
      driftPhase: rand(0, Math.PI * 2),
      lum: luminosity,
      twinkle: rand(0.008, 0.03),
      twinklePhase: rand(0, Math.PI * 2),
    });
  }
  return nodes;
}

function buildRipples(width, height) {
  const count = Math.max(3, Math.floor(width / 520));
  const ripples = [];
  for (let i = 0; i < count; i += 1) {
    ripples.push({
      x: rand(width * 0.18, width * 0.82),
      y: rand(height * 0.2, height * 0.8),
      base: rand(84, 196),
      speed: rand(0.004, 0.009),
      phase: rand(0, Math.PI * 2),
      alpha: rand(0.024, 0.052),
    });
  }
  return ripples;
}

function buildDrifters(width, height) {
  const count = Math.max(6, Math.floor(width / 260));
  const lights = [];
  for (let i = 0; i < count; i += 1) {
    lights.push({
      x: rand(0, width),
      y: rand(0, height),
      vx: rand(-0.04, 0.04),
      vy: rand(-0.03, 0.03),
      radius: rand(24, 58),
      alpha: rand(0.03, 0.08),
      signal: rand(0.2, 1),
    });
  }
  return lights;
}

export function initDataCosmos(canvas) {
  if (!canvas || !(canvas instanceof HTMLCanvasElement)) {
    return () => {};
  }

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return () => {};
  }

  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return () => {};
  }

  let width = 0;
  let height = 0;
  let rafId = null;
  let tick = 0;
  let nodes = [];
  let ripples = [];
  let drifters = [];

  const pointer = {
    x: -1000,
    y: -1000,
    active: false,
  };

  function resize() {
    width = window.innerWidth;
    height = window.innerHeight;

    const dpr = Math.min(window.devicePixelRatio || 1, DPR_MAX);
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const nodeCount = Math.max(22, Math.floor((width * height) / NODE_DENSITY));
    nodes = buildNodes(nodeCount, width, height);
    ripples = buildRipples(width, height);
    drifters = buildDrifters(width, height);
  }

  function drawNearVacuum() {
    const g1 = ctx.createRadialGradient(width * 0.82, height * 0.18, 0, width * 0.82, height * 0.18, width * 0.7);
    g1.addColorStop(0, "rgba(150, 134, 171, 0.11)");
    g1.addColorStop(0.5, "rgba(112, 102, 130, 0.06)");
    g1.addColorStop(1, "rgba(112, 102, 130, 0)");
    ctx.fillStyle = g1;
    ctx.fillRect(0, 0, width, height);

    const g2 = ctx.createRadialGradient(width * 0.2, height * 0.76, 0, width * 0.2, height * 0.76, width * 0.66);
    g2.addColorStop(0, "rgba(188, 193, 201, 0.06)");
    g2.addColorStop(1, "rgba(188, 193, 201, 0)");
    ctx.fillStyle = g2;
    ctx.fillRect(0, 0, width, height);
  }

  function drawDrifters() {
    drifters.forEach((light) => {
      light.x += light.vx;
      light.y += light.vy;

      if (light.x < -40) light.x = width + 40;
      if (light.x > width + 40) light.x = -40;
      if (light.y < -40) light.y = height + 40;
      if (light.y > height + 40) light.y = -40;

      const tone = pickTone(light.signal);
      const glow = ctx.createRadialGradient(light.x, light.y, 0, light.x, light.y, light.radius);
      glow.addColorStop(0, `rgba(${tone[0]}, ${tone[1]}, ${tone[2]}, ${light.alpha})`);
      glow.addColorStop(1, `rgba(${tone[0]}, ${tone[1]}, ${tone[2]}, 0)`);
      ctx.fillStyle = glow;
      ctx.fillRect(light.x - light.radius, light.y - light.radius, light.radius * 2, light.radius * 2);
    });
  }

  function drawRipples() {
    ripples.forEach((ripple) => {
      ripple.phase += ripple.speed;
      const wave = 0.5 + 0.5 * Math.sin(ripple.phase + tick * 0.012);
      const tone = pickTone(ripple.alpha * 12.8);

      for (let i = 0; i < 3; i += 1) {
        const radius = ripple.base + i * 22 + wave * 18;
        ctx.beginPath();
        ctx.lineWidth = 0.6;
        ctx.strokeStyle = `rgba(${tone[0]}, ${tone[1]}, ${tone[2]}, ${ripple.alpha * (1 - i * 0.28)})`;
        ctx.arc(ripple.x, ripple.y, radius, 0, Math.PI * 2);
        ctx.stroke();
      }
    });
  }

  function updateAndDrawNodes() {
    const breath = 0.5 + 0.5 * Math.sin(tick * 0.009);
    const clusterX = width * (0.5 + Math.sin(tick * 0.0022) * 0.08);
    const clusterY = height * (0.5 + Math.cos(tick * 0.0018) * 0.06);

    for (let i = 0; i < nodes.length; i += 1) {
      const a = nodes[i];
      const aggregateForce = (breath - 0.5) * 0.004;

      const dxc = clusterX - a.x;
      const dyc = clusterY - a.y;
      const distCenter = Math.max(1, Math.hypot(dxc, dyc));
      a.vx += (dxc / distCenter) * aggregateForce;
      a.vy += (dyc / distCenter) * aggregateForce;

      const driftWave = Math.sin(tick * a.drift + a.driftPhase) * 0.01;
      a.vx += driftWave;
      a.vy -= driftWave * 0.7;

      if (pointer.active) {
        const dxp = pointer.x - a.x;
        const dyp = pointer.y - a.y;
        const dpp = Math.hypot(dxp, dyp);
        if (dpp < POINTER_GRAVITY_RADIUS) {
          const pull = (1 - dpp / POINTER_GRAVITY_RADIUS) * 0.0018;
          a.vx += (dxp / (dpp || 1)) * pull;
          a.vy += (dyp / (dpp || 1)) * pull;
        }
      }

      a.vx *= 0.987;
      a.vy *= 0.987;
      a.x += a.vx;
      a.y += a.vy;

      if (a.x < -10) a.x = width + 10;
      if (a.x > width + 10) a.x = -10;
      if (a.y < -10) a.y = height + 10;
      if (a.y > height + 10) a.y = -10;

      for (let j = i + 1; j < nodes.length; j += 1) {
        const b = nodes[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dist = Math.hypot(dx, dy);
        const activeLinkDistance = BASE_LINK_DISTANCE + breath * 26;

        if (dist < activeLinkDistance) {
          const alpha = (1 - dist / activeLinkDistance) * (0.08 + (a.lum + b.lum) * 0.08);
          const tone = pickTone((a.signal + b.signal) * 0.5);
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = `rgba(${tone[0]}, ${tone[1]}, ${tone[2]}, ${alpha})`;
          ctx.lineWidth = 0.32 + ((a.lum + b.lum) * 0.25);
          ctx.stroke();
        }
      }

      const pulse = 0.28 + 0.42 * Math.sin(tick * (0.018 + a.twinkle) + a.twinklePhase);
      const tone = pickTone(a.signal);
      ctx.beginPath();
      ctx.fillStyle = `rgba(${tone[0]}, ${tone[1]}, ${tone[2]}, ${0.07 + a.lum * 0.36 + pulse * 0.2})`;
      ctx.arc(a.x, a.y, a.r + pulse * (0.22 + a.lum * 0.42), 0, Math.PI * 2);
      ctx.fill();

      if (a.lum > 0.78) {
        const halo = ctx.createRadialGradient(a.x, a.y, 0, a.x, a.y, a.r * 3.4);
        halo.addColorStop(0, `rgba(${tone[0]}, ${tone[1]}, ${tone[2]}, ${0.13 + pulse * 0.06})`);
        halo.addColorStop(1, `rgba(${tone[0]}, ${tone[1]}, ${tone[2]}, 0)`);
        ctx.fillStyle = halo;
        ctx.fillRect(a.x - a.r * 3.4, a.y - a.r * 3.4, a.r * 6.8, a.r * 6.8);
      }
    }
  }

  function render() {
    tick += 1;
    ctx.clearRect(0, 0, width, height);

    drawNearVacuum();
    drawDrifters();
    drawRipples();
    updateAndDrawNodes();

    rafId = window.requestAnimationFrame(render);
  }

  function onVisibilityChange() {
    if (document.hidden && rafId) {
      window.cancelAnimationFrame(rafId);
      rafId = null;
    } else if (!document.hidden && !rafId) {
      rafId = window.requestAnimationFrame(render);
    }
  }

  resize();
  rafId = window.requestAnimationFrame(render);

  const onPointerMove = (event) => {
    pointer.x = event.clientX;
    pointer.y = event.clientY;
    pointer.active = true;
  };

  const onPointerLeave = () => {
    pointer.active = false;
  };

  const onResize = () => resize();
  window.addEventListener("resize", onResize);
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerleave", onPointerLeave);
  document.addEventListener("visibilitychange", onVisibilityChange);

  return () => {
    if (rafId) {
      window.cancelAnimationFrame(rafId);
      rafId = null;
    }
    window.removeEventListener("resize", onResize);
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerleave", onPointerLeave);
    document.removeEventListener("visibilitychange", onVisibilityChange);
  };
}
