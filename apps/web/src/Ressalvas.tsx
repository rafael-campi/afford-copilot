import type { Ressalva } from './api'

export function Ressalvas({ ressalvas }: { ressalvas: Ressalva[] }) {
  if (ressalvas.length === 0) return null
  return (
    <ul className="ressalvas">
      {ressalvas.map((r) => (
        <li key={r.codigo} className="ressalva">
          {r.texto}
        </li>
      ))}
    </ul>
  )
}
