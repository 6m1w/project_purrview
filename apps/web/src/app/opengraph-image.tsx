import { ImageResponse } from "next/og";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

export const alt = "PurrView — AI-Powered Care for 5 Beloved Cats";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OGImage() {
  // Read the headshot file as base64 for embedding
  const imgPath = join(process.cwd(), "public", "majiang_headshot.jpeg");
  const imgBuffer = await readFile(imgPath);
  const imgBase64 = `data:image/jpeg;base64,${imgBuffer.toString("base64")}`;

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          backgroundColor: "#f4f4f0",
        }}
      >
        {/* Left: photo */}
        <div
          style={{
            width: 630,
            height: 630,
            display: "flex",
            overflow: "hidden",
          }}
        >
          <img
            src={imgBase64}
            width={630}
            height={630}
            style={{ objectFit: "cover" }}
          />
        </div>

        {/* Right: text */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            padding: "60px 50px",
            borderLeft: "6px solid #000",
          }}
        >
          <div
            style={{
              fontSize: 72,
              fontWeight: 700,
              letterSpacing: "-0.02em",
              lineHeight: 1.1,
              color: "#000",
            }}
          >
            PurrView
          </div>
          <div
            style={{
              marginTop: 24,
              fontSize: 24,
              lineHeight: 1.5,
              color: "#000000aa",
            }}
          >
            AI-powered care for 5 beloved rescue cats
          </div>
          <div
            style={{
              marginTop: 40,
              display: "flex",
              gap: 12,
            }}
          >
            {["🐱", "🐱", "🐱", "🐱", "🐱"].map((_, i) => (
              <div
                key={i}
                style={{
                  width: 16,
                  height: 16,
                  backgroundColor: ["#f59e0b", "#B19379", "#ef4444", "#22c55e", "#1a1a1a"][i],
                  border: "2px solid #000",
                }}
              />
            ))}
          </div>
        </div>
      </div>
    ),
    { ...size }
  );
}
