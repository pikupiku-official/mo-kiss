// Generate small, loopable rain beds without a runtime codec dependency.
// The result is intentionally ambience, not a one-shot sound effect.
const fs = require("fs");
const path = require("path");

const RATE = 44100;
const SECONDS = 12;
const CHANNELS = 2;
const COUNT = RATE * SECONDS;
const FADE = RATE / 4;

function rng(seed) {
  let value = seed >>> 0;
  return () => {
    value = (value * 1664525 + 1013904223) >>> 0;
    return (value / 0x100000000) * 2 - 1;
  };
}

function createBed(density, level, seed) {
  const random = rng(seed);
  const left = new Float32Array(COUNT);
  const right = new Float32Array(COUNT);
  let low = 0;
  let drops = 0;
  let dropsRight = 0;
  for (let i = 0; i < COUNT; i += 1) {
    const white = random();
    low = low * 0.996 + white * 0.004;
    if (Math.abs(random()) < density) {
      drops += (0.25 + Math.abs(random()) * 0.75) * (random() < 0 ? -1 : 1);
    }
    if (Math.abs(random()) < density * 0.83) {
      dropsRight += (0.25 + Math.abs(random()) * 0.75) * (random() < 0 ? -1 : 1);
    }
    drops *= 0.994;
    dropsRight *= 0.994;
    const hiss = (white - low) * 0.11;
    const rumble = low * 0.22;
    left[i] = (rumble + hiss + drops * 0.13) * level;
    right[i] = (rumble * 0.96 + random() * 0.025 + hiss + dropsRight * 0.13) * level;
  }

  // Equal-power-ish crossfade makes the end join the beginning cleanly.
  for (let i = 0; i < FADE; i += 1) {
    const startWeight = i / FADE;
    const endIndex = COUNT - FADE + i;
    const leftValue = left[endIndex] * (1 - startWeight) + left[i] * startWeight;
    const rightValue = right[endIndex] * (1 - startWeight) + right[i] * startWeight;
    left[i] = leftValue;
    right[i] = rightValue;
    left[endIndex] = leftValue;
    right[endIndex] = rightValue;
  }
  return { left, right };
}

function writeWav(filename, bed) {
  const dataSize = COUNT * CHANNELS * 2;
  const buffer = Buffer.alloc(44 + dataSize);
  buffer.write("RIFF", 0, "ascii");
  buffer.writeUInt32LE(36 + dataSize, 4);
  buffer.write("WAVEfmt ", 8, "ascii");
  buffer.writeUInt32LE(16, 16);
  buffer.writeUInt16LE(1, 20);
  buffer.writeUInt16LE(CHANNELS, 22);
  buffer.writeUInt32LE(RATE, 24);
  buffer.writeUInt32LE(RATE * CHANNELS * 2, 28);
  buffer.writeUInt16LE(CHANNELS * 2, 32);
  buffer.writeUInt16LE(16, 34);
  buffer.write("data", 36, "ascii");
  buffer.writeUInt32LE(dataSize, 40);
  let offset = 44;
  for (let i = 0; i < COUNT; i += 1) {
    buffer.writeInt16LE(Math.max(-32767, Math.min(32767, Math.round(bed.left[i] * 32767))), offset);
    offset += 2;
    buffer.writeInt16LE(Math.max(-32767, Math.min(32767, Math.round(bed.right[i] * 32767))), offset);
    offset += 2;
  }
  fs.writeFileSync(filename, buffer);
}

const outputDir = path.join(__dirname, "..", "sounds", "ambience");
fs.mkdirSync(outputDir, { recursive: true });
writeWav(path.join(outputDir, "normal_rain.wav"), createBed(0.005, 0.30, 0x12345678));
writeWav(path.join(outputDir, "heavy_rain.wav"), createBed(0.012, 0.52, 0x9abcdef0));
console.log(`generated rain beds in ${outputDir}`);
