# Unity Integration Guide

## What the Exporter Produces
- `<Name>_sprites/` — Atlas PNG files to import
- `<Name>_atlas.json` — Frame metadata per animation clip
- `<Name>_animator.json` — AnimatorController stub (JSON)
- `README.md` — Setup instructions

## Import Steps
1. Copy `<Name>_sprites/` into `Assets/Sprites/<Name>/`
2. In Unity Inspector for each PNG: set **Sprite Mode** to **Multiple**
3. Open **Sprite Editor** → Slice → Grid By Cell Size (use `frame_w × frame_h` from atlas JSON)
4. Create `AnimationClip` assets for each clip using the sliced sprites
5. Create an `AnimatorController` and reference `<Name>_animator.json` for state machine layout

## Script Example (C#)
```csharp
using UnityEngine;

public class CharacterAnimator : MonoBehaviour
{
    private Animator _animator;
    static readonly int Walk = Animator.StringToHash("Walk");
    static readonly int Attack = Animator.StringToHash("Attack");

    void Start() => _animator = GetComponent<Animator>();

    public void PlayWalk() => _animator.SetBool(Walk, true);
    public void PlayAttack() => _animator.SetTrigger(Attack);
}
```

## Sprite Atlas (Optional)
For production, use Unity's **Sprite Atlas** asset to pack all clips into a single texture atlas for better GPU performance.
