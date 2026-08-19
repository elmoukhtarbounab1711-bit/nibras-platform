"""
نقطة تشغيل الخادم.

الاستخدام:
    python3 -m app.seed        # تعبئة قاعدة البيانات ببيانات نموذجية (مرة واحدة)
    python3 run.py             # تشغيل الخادم على http://localhost:8000

وضع التصحيح (debug) مُعطَّل افتراضيًا؛ لتفعيله محليًا فقط:
    NIBRAS_DEBUG=1 python3 run.py
"""
import os
from app import config, create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=config.DEBUG, use_reloader=False)
