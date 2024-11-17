example:

```bash
python simulate.py --visualize --simulation_steps=20000 --scenario='DifferentDensity'
```

```bash
python simulate.py --visualize --simulation_steps=20000
```

## Examples

### DifferentDensity
![](./videos/DifferentDensity.gif)

### Flood
![](./videos/Flood.gif)


## Features Checklist

- Basic Types
  - [ ] Rigid Body
  - [x] Deformable Body
  - [ ] Cloth
  - [x] Fluid
  - [x] Elastoplastic Objects
- Coupling
  - [ ] Solid-Solid
  - [ ] Solid-Fluid
  - [ ] Solid-Cloth
  - [x] Fluid-Fluid
  - [ ] Fluid-Cloth
  - [ ] Cloth-Cloth
- Geometry
  - Trivial Geometry
    - [x] Cube
    - [x] Ball
    - [ ] ...
  - Complex (mesh based or equation based) geometry
- Acceleration (Need to analysis the bottleneck and prove your acceleration ratio)
  - [ ] Algorithm acceleration
  - [ ] Multi-thread acceleration
  - [ ] GPU acceleration
- Control
  - [x] Customized scene configuration
    - Can use config files to customize scene configuration.
  - [ ] Interactive scene
- Rendering
  - [x] Now use Blender to render