"use client";

import { useRef, useEffect, useCallback } from "react";

export interface ScanlineConfig {
  lineDensity: number;
  widthRatio: number;
  jitter: number;
  jitterSpeed: number;
  offsetX: number;
  offsetY: number;
  zoom: number;
  alphaThreshold: number;
  minDarkness: number;
  bgLineOpacity: number;
  cropLeft: number;
}

interface ScanlineCanvasProps {
  videoSrc: string;
  config?: Partial<ScanlineConfig>;
  className?: string;
  onVideoEnd?: () => void;
}

// Default configuration (tuned via shader-debug.html for majiang)
const DEFAULT_CONFIG: ScanlineConfig = {
  lineDensity: 6,
  widthRatio: 0.7,
  jitter: 0,
  jitterSpeed: 15,
  offsetX: -0.1,
  offsetY: -0.03,
  zoom: 1.0,
  alphaThreshold: 0.7,
  minDarkness: 0.3,
  bgLineOpacity: 0.9,
  cropLeft: 0,
};

const BG = [0.92, 0.92, 0.904] as const; // bgBright=0.92
const FG = [0.1, 0.1, 0.1] as const; // fgBright=0.1

const VERT_SRC = `
attribute vec2 a_pos;
varying vec2 v_uv;
void main() {
  v_uv = a_pos * 0.5 + 0.5;
  gl_Position = vec4(a_pos, 0.0, 1.0);
}`;

const FRAG_SRC = `
precision mediump float;
varying vec2 v_uv;
uniform sampler2D u_tex;
uniform vec2 u_resolution;
uniform vec2 u_videoSize;
uniform float u_time;
uniform float u_lineDensity;
uniform float u_widthRatio;
uniform float u_jitterPx;
uniform float u_jitterSpeed;
uniform float u_offsetX;
uniform float u_offsetY;
uniform float u_zoom;
uniform float u_alphaThreshold;
uniform float u_minDarkness;
uniform float u_bgLineOpacity;
uniform float u_cropLeft;
uniform vec3 u_fg;
uniform vec3 u_bg;

float hash(float n) {
  return fract(sin(n) * 43758.5453123);
}

void main() {
  vec2 uv = v_uv;
  float yPx = uv.y * u_resolution.y;

  // Cover mode UV mapping (fill canvas, crop excess)
  float canvasAspect = u_resolution.x / u_resolution.y;
  float videoAspect = u_videoSize.x / u_videoSize.y;
  vec2 sampleUV = uv;
  if (videoAspect > canvasAspect) {
    float scale = canvasAspect / videoAspect;
    sampleUV.x = (uv.x - 0.5) * scale + 0.5;
  } else {
    float scale = videoAspect / canvasAspect;
    sampleUV.y = (uv.y - 0.5) * scale + 0.5;
  }

  // Zoom and offset (negative offsetX = push content right)
  sampleUV = (sampleUV - 0.5) / u_zoom + 0.5;
  sampleUV.x += u_offsetX;
  sampleUV.y += u_offsetY;

  // Scanline row calculation
  float lineGapPx = max(2.0, u_lineDensity);
  float row = floor(yPx / lineGapPx);
  float local = mod(yPx, lineGapPx);

  // Horizontal jitter per scan-line row
  float jitterSeed = row * 19.19 + floor(u_time * u_jitterSpeed);
  float n = hash(jitterSeed) * 2.0 - 1.0;
  float wobble = sin(u_time * 8.0 + row * 0.45) * 0.5;
  float jitterNorm = (n * 0.7 + wobble * 0.3) * (u_jitterPx / u_resolution.x);
  sampleUV.x += jitterNorm;

  // Out of bounds -> background with subtle scanlines
  if (sampleUV.x < 0.0 || sampleUV.x > 1.0 || sampleUV.y < 0.0 || sampleUV.y > 1.0) {
    float bgLineWidth = 0.7;
    if (local <= bgLineWidth) {
      gl_FragColor = vec4(u_bg * u_bgLineOpacity, 1.0);
    } else {
      gl_FragColor = vec4(u_bg, 1.0);
    }
    return;
  }

  // Crop left edge (removes black border artifacts)
  if (u_cropLeft > 0.0 && sampleUV.x < u_cropLeft) {
    float bgLineWidth = 0.7;
    if (local <= bgLineWidth) {
      gl_FragColor = vec4(u_bg * u_bgLineOpacity, 1.0);
    } else {
      gl_FragColor = vec4(u_bg, 1.0);
    }
    return;
  }

  sampleUV = clamp(sampleUV, 0.0, 1.0);
  vec4 c = texture2D(u_tex, sampleUV);
  float luma = dot(c.rgb, vec3(0.2126, 0.7152, 0.0722));
  float darkness = 1.0 - luma;

  // Treat as background if: transparent OR too bright (noise cleanup)
  if (c.a < u_alphaThreshold || darkness < u_minDarkness) {
    float bgLineWidth = 0.7;
    if (local <= bgLineWidth) {
      gl_FragColor = vec4(u_bg * u_bgLineOpacity, 1.0);
    } else {
      gl_FragColor = vec4(u_bg, 1.0);
    }
    return;
  }

  // Variable line width: dark pixels -> thick lines, light -> thin
  float maxLineWidth = lineGapPx * u_widthRatio;
  float lineWidth = max(0.5, darkness * maxLineWidth);

  if (local > lineWidth) {
    gl_FragColor = vec4(u_bg, 1.0);
    return;
  }

  gl_FragColor = vec4(u_fg, 1.0);
}`;

// --- WebGL helpers ---

function compileShader(gl: WebGLRenderingContext, type: number, src: string) {
  const s = gl.createShader(type)!;
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    const info = gl.getShaderInfoLog(s);
    gl.deleteShader(s);
    throw new Error(`Shader compile: ${info}`);
  }
  return s;
}

function linkProgram(gl: WebGLRenderingContext, vs: WebGLShader, fs: WebGLShader) {
  const p = gl.createProgram()!;
  gl.attachShader(p, vs);
  gl.attachShader(p, fs);
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
    const info = gl.getProgramInfoLog(p);
    gl.deleteProgram(p);
    throw new Error(`Program link: ${info}`);
  }
  return p;
}

// --- Component ---

export function ScanlineCanvas({ videoSrc, config: configOverride, className, onVideoEnd }: ScanlineCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const configRef = useRef<ScanlineConfig>({ ...DEFAULT_CONFIG, ...configOverride });
  const onVideoEndRef = useRef(onVideoEnd);

  // Keep refs in sync with props
  configRef.current = { ...DEFAULT_CONFIG, ...configOverride };
  onVideoEndRef.current = onVideoEnd;

  // Handle video ended event
  const handleEnded = useCallback(() => {
    onVideoEndRef.current?.();
  }, []);

  // WebGL setup — runs once on mount, never tears down until unmount
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext("webgl", { alpha: false, antialias: false });
    if (!gl) {
      console.error("WebGL not available");
      return;
    }

    // Compile & link
    const program = linkProgram(
      gl,
      compileShader(gl, gl.VERTEX_SHADER, VERT_SRC),
      compileShader(gl, gl.FRAGMENT_SHADER, FRAG_SRC),
    );
    gl.useProgram(program);

    // Fullscreen quad
    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]),
      gl.STATIC_DRAW,
    );
    const aPos = gl.getAttribLocation(program, "a_pos");
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 0, 0);

    // Uniforms
    const u = {
      tex: gl.getUniformLocation(program, "u_tex"),
      resolution: gl.getUniformLocation(program, "u_resolution"),
      videoSize: gl.getUniformLocation(program, "u_videoSize"),
      time: gl.getUniformLocation(program, "u_time"),
      lineDensity: gl.getUniformLocation(program, "u_lineDensity"),
      widthRatio: gl.getUniformLocation(program, "u_widthRatio"),
      jitterPx: gl.getUniformLocation(program, "u_jitterPx"),
      jitterSpeed: gl.getUniformLocation(program, "u_jitterSpeed"),
      offsetX: gl.getUniformLocation(program, "u_offsetX"),
      offsetY: gl.getUniformLocation(program, "u_offsetY"),
      zoom: gl.getUniformLocation(program, "u_zoom"),
      alphaThreshold: gl.getUniformLocation(program, "u_alphaThreshold"),
      minDarkness: gl.getUniformLocation(program, "u_minDarkness"),
      bgLineOpacity: gl.getUniformLocation(program, "u_bgLineOpacity"),
      cropLeft: gl.getUniformLocation(program, "u_cropLeft"),
      fg: gl.getUniformLocation(program, "u_fg"),
      bg: gl.getUniformLocation(program, "u_bg"),
    };

    // Texture
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.uniform1i(u.tex, 0);

    // Static uniforms
    gl.uniform3f(u.fg, FG[0], FG[1], FG[2]);
    gl.uniform3f(u.bg, BG[0], BG[1], BG[2]);

    // Create video element (persists across source changes)
    const video = document.createElement("video");
    video.muted = true;
    video.playsInline = true;
    video.crossOrigin = "anonymous";
    video.style.display = "none";
    document.body.appendChild(video);
    videoRef.current = video;

    // Resize canvas buffer to CSS size × DPR
    function resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const rect = canvas!.getBoundingClientRect();
      const w = Math.floor(rect.width * dpr);
      const h = Math.floor(rect.height * dpr);
      if (canvas!.width !== w || canvas!.height !== h) {
        canvas!.width = w;
        canvas!.height = h;
      }
      gl!.viewport(0, 0, w, h);
    }

    // Render loop — reads config from ref each frame
    let raf = 0;
    function draw(timeMs: number) {
      raf = requestAnimationFrame(draw);
      resize();

      if (video.readyState < 2 || video.videoWidth === 0) return;

      const cfg = configRef.current;

      gl!.activeTexture(gl!.TEXTURE0);
      gl!.bindTexture(gl!.TEXTURE_2D, tex);
      gl!.pixelStorei(gl!.UNPACK_FLIP_Y_WEBGL, 1);
      gl!.texImage2D(gl!.TEXTURE_2D, 0, gl!.RGBA, gl!.RGBA, gl!.UNSIGNED_BYTE, video);

      gl!.uniform2f(u.resolution, canvas!.width, canvas!.height);
      gl!.uniform2f(u.videoSize, video.videoWidth, video.videoHeight);
      gl!.uniform1f(u.time, timeMs * 0.001);
      gl!.uniform1f(u.lineDensity, cfg.lineDensity);
      gl!.uniform1f(u.widthRatio, cfg.widthRatio);
      gl!.uniform1f(u.jitterPx, cfg.jitter);
      gl!.uniform1f(u.jitterSpeed, cfg.jitterSpeed);
      gl!.uniform1f(u.offsetX, cfg.offsetX);
      gl!.uniform1f(u.offsetY, cfg.offsetY);
      gl!.uniform1f(u.zoom, cfg.zoom);
      gl!.uniform1f(u.alphaThreshold, cfg.alphaThreshold);
      gl!.uniform1f(u.minDarkness, cfg.minDarkness);
      gl!.uniform1f(u.bgLineOpacity, cfg.bgLineOpacity);
      gl!.uniform1f(u.cropLeft, cfg.cropLeft);

      gl!.drawArrays(gl!.TRIANGLE_STRIP, 0, 4);
    }
    raf = requestAnimationFrame(draw);

    // Click-to-play fallback for autoplay policy
    const onClick = () => {
      if (video.paused) video.play();
    };
    document.body.addEventListener("click", onClick);

    // Cleanup on unmount only
    return () => {
      cancelAnimationFrame(raf);
      document.body.removeEventListener("click", onClick);
      video.removeEventListener("ended", handleEnded);
      video.pause();
      video.src = "";
      video.remove();
      videoRef.current = null;
      gl!.deleteTexture(tex);
      gl!.deleteBuffer(buf);
      gl!.deleteProgram(program);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Mount once — never re-run

  // Hot-swap video source without destroying WebGL context
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    video.removeEventListener("ended", handleEnded);
    video.loop = !onVideoEndRef.current;
    video.addEventListener("ended", handleEnded);
    video.src = videoSrc;
    video.load();
    video.play().catch(() => {});
  }, [videoSrc, handleEnded]);

  return <canvas ref={canvasRef} className={className} />;
}
