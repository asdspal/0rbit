#!/usr/bin/env node

/**
 * 0G Storage upload helper.
 *
 * Invoked from Python via `node agents/scripts/0g_upload.js <filePath> [--filename name]`.
 * Requires `@0gfoundation/0g-storage-ts-sdk` and `ethers` to be installed in the
 * workspace (per blueprint Section 4.1).
 */

const fs = require('fs');
const path = require('path');

function parseArgs(argv) {
  if (!argv.length) {
    throw new Error('Missing file path argument');
  }

  const parsed = {
    filePath: argv[0],
    filename: null,
  };

  for (let i = 1; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--filename') {
      if (i + 1 >= argv.length) {
        throw new Error('--filename flag requires a value');
      }
      parsed.filename = argv[i + 1];
      i += 1;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return parsed;
}

async function main() {
  const argv = process.argv.slice(2);
  const { filePath, filename } = parseArgs(argv);

  const absolutePath = path.resolve(filePath);
  await fs.promises.access(absolutePath, fs.constants.R_OK);

  const baseUrl = process.env.OG_STORAGE_URL || 'https://storage-testnet.0g.ai';
  const apiKey = process.env.OG_STORAGE_API_KEY;

  let StorageClient;
  try {
    ({ StorageClient } = require('@0gfoundation/0g-storage-ts-sdk'));
  } catch (err) {
    throw new Error('Failed to load @0gfoundation/0g-storage-ts-sdk. Did you run `npm install @0gfoundation/0g-storage-ts-sdk ethers`?');
  }

  if (typeof StorageClient !== 'function') {
    throw new Error('Invalid SDK import: StorageClient class not found');
  }

  const client = new StorageClient({ baseUrl, apiKey });
  const uploadFilename = filename || path.basename(absolutePath);

  const result = await client.uploadFile(absolutePath, { filename: uploadFilename });
  const merkleRoot = typeof result === 'string' ? result : result?.merkleRoot || result?.hash;

  if (!merkleRoot) {
    throw new Error('0G SDK returned an empty response');
  }

  process.stdout.write(`${merkleRoot}\n`);
}

main().catch((err) => {
  const message = err?.stack || err?.message || String(err);
  process.stderr.write(`${message}\n`);
  process.exit(1);
});
