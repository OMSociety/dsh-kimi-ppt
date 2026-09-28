/**
 * Cordis host plugin for dsh-kimi-ppt.
 *
 * One job: register the bundled `skills/kimi-ppt` as a DSH skill so the model
 * can load it. DSH discovers skills one level deep under a fixed set of roots,
 * and a path inside `node_modules` is none of them — so shipping `skills/` in
 * the package file list puts the files on disk where nothing will ever look at
 * them. Registering the directory as a skill is what turns them into a skill.
 *
 * Registration path: `ctx.skills.register(def)` is the runtime-skill entry on
 * the SkillRegistry service, and it needs `ctx.skills` to be *injected* —
 * Cordis refuses a bare `ctx.skills` access when `inject` does not declare it
 * ("cannot get property 'skills' without inject"), so we declare
 * `inject = ['skills']`. The skill is registered best-effort: if the file is
 * absent or the host exposes no skill hook, we warn and still load rather
 * than failing the whole plugin tree.
 */
import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const name = 'dsh-kimi-ppt'
export const inject = ['skills']

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const SKILL_DIR = path.join(ROOT, 'skills', 'kimi-ppt')
const SKILL_FILE = path.join(SKILL_DIR, 'SKILL.md')

/** Minimal YAML-frontmatter reader for the skill's own `key: value` block. */
function readSkillFrontmatter(source) {
  const m = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/.exec(source)
  if (!m) return {}
  const out = {}
  for (const line of m[1].split(/\r?\n/)) {
    const kv = /^([A-Za-z0-9_-]+):\s*(.*)$/.exec(line)
    if (kv) out[kv[1]] = kv[2].trim()
  }
  return out
}

function registerSkill(ctx) {
  if (!existsSync(SKILL_FILE)) return () => {}
  try {
    const source = readFileSync(SKILL_FILE, 'utf8')
    const frontmatter = readSkillFrontmatter(source)
    const body = source.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n?/, '')
    const off = ctx.skills.register({
      name: frontmatter.name,
      description: frontmatter.description,
      ...frontmatter.whenToUse !== void 0 ? { whenToUse: frontmatter.whenToUse } : {},
      content: body.trim(),
      // `register()` fills `provider` but not `source`, and the registry's load path
      // (`SkillRegistry.get()` -> `validateDefinition`) requires both to be strings:
      // without `source` the skill shows up in the catalog and then throws on first
      // load with `loaded skill "..." source must be a string`.
      source: 'bundled',
      resourceBase: { kind: 'directory', path: SKILL_DIR }
    })
    return typeof off === 'function' ? off : () => {}
  } catch (err) {
    ctx.logger?.warn?.(`[dsh-kimi-ppt] could not register the skill: ${err.message}`)
    return () => {}
  }
}

export function apply(ctx) {
  const unregister = registerSkill(ctx)
  ctx.effect(() => () => {
    unregister()
  })
}
