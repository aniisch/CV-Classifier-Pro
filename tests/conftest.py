import os
import tempfile

# Les tests ne doivent jamais toucher la vraie base (data/ ou dossier utilisateur).
os.environ.setdefault("CV_CLASSIFIER_DATA_DIR", tempfile.mkdtemp(prefix="cvc_tests_"))
