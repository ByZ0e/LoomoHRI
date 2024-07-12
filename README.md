# LoomoHRI
A react based web demo for Loomo Human-Robot-Interaction(HRI)

Top: Caption and VQA tasks based on the RGB-D video streams observed by Loomo.

Bottom: Visual Grounding task based on the reconstructed 3D scene.

https://github.com/user-attachments/assets/25b6a556-474a-4b33-8ff8-460107a695cb


## Quick Start

### Installation

Use npm to install the tool into your react project. 
```
cd Loomo-Front-End
npm i Loomo-Front-End --save
```

### Data Preperation
Get SG results like 'localmode_locobot_output'.
Run scripts in 'script' to get all related caption & VQA files.
- SG_convert: get annotation files & caption files.
- QA_generator: get QA files.

### Start
```
npm start
```

## Ackonwledgements
We are grateful to [react-annotation-tool](https://github.com/bennylin77/react-annotation-tool), on which our codes are developed.
