"""
Совместимый запуск проектных RF-моделей на синтетических метриках.

Старая версия этого файла работала с задачным synthetic_tasks.csv, поэтому название
"risk" вводило в заблуждение. Актуальная проектная версия находится в
03_rf_synth_model.py и обучает две модели: длительность и Schedule Risk Ratio.
"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).with_name("03_rf_synth_model.py")),
        run_name="__main__",
    )
