import { build } from 'esbuild';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const output = resolve(process.argv[2]);
const result = await build({
  absWorkingDir: root,
  entryPoints: ['src/App.jsx'],
  outdir: resolve(output, 'assets'),
  entryNames: 'app-[hash]',
  bundle: true,
  minify: true,
  jsx: 'automatic',
  format: 'iife',
  target: ['es2022'],
  define: { 'process.env.NODE_ENV': '"production"' },
  legalComments: 'inline',
  metafile: true,
  logLevel: 'silent',
});
const entry = Object.entries(result.metafile.outputs).find(([, info]) => info.entryPoint);
console.log(JSON.stringify({ script: `assets/${entry[0].split('/').at(-1)}` }));
