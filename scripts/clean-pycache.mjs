/**
 * Drop Python bytecode caches and pytest caches before packing.
 *
 * `npm pack` / `npm publish` ship whatever sits in the working tree, and this
 * package declares a `files` whitelist — in that mode npm applies neither
 * .gitignore nor .npmignore (measured: a stray `__pycache__/x.pyc` survives
 * both, and only disappears once the directory is gone from disk). So caches
 * left behind by a test run would ship, and removing them here is the only
 * reliable point of control.
 */
import { readdirSync, rmSync } from 'node:fs'
import { join } from 'node:path'

const CACHE_DIRS = new Set(['__pycache__', '.pytest_cache'])

function clean(dir) {
  let entries
  try {
    entries = readdirSync(dir, { withFileTypes: true })
  } catch (error) {
    console.warn(`prepack: skipped ${dir} (${error.code ?? error.message})`)
    return
  }
  for (const entry of entries) {
    if (!entry.isDirectory()) continue
    const path = join(dir, entry.name)
    if (CACHE_DIRS.has(entry.name)) rmSync(path, { recursive: true, force: true })
    else if (entry.name !== 'node_modules' && entry.name !== '.git') clean(path)
  }
}

clean(process.cwd())
