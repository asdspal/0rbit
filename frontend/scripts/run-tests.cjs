#!/usr/bin/env node
const { spawn } = require('node:child_process')

const args = process.argv.slice(2)

let pattern
const filteredArgs = []

for (let i = 0; i < args.length; i += 1) {
  const current = args[i]

  if (current.startsWith('--testPathPattern=')) {
    pattern = current.split('=')[1]
    continue
  }

  if (current === '--testPathPattern') {
    pattern = args[i + 1]
    i += 1
    continue
  }

  filteredArgs.push(current)
}

const vitestArgs = ['vitest', 'run']

if (pattern) {
  vitestArgs.push(pattern)
}

vitestArgs.push(...filteredArgs)

const child = spawn('npx', vitestArgs, { stdio: 'inherit', shell: false })

child.on('exit', (code) => {
  process.exit(code === null ? 1 : code)
})
