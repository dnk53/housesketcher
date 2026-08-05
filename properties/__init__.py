# ________________________________________________________________________________________________
# PROPERTIES PAKET
# ________________________________________________________________________________________________

from . import huvudmatt
from . import platta
from . import vagg_settings  # <-- FLYTTAS FÖRE vagg
from . import vagg
from . import tak
from . import bjalklag
from . import fonster
from . import dorr

classes = (
    huvudmatt.BT_HuvudmåttProperties,
    platta.BT_PlattaProperties,
    vagg_settings.BT_VaggSettingsProperties,  # <-- REGISTRERAS FÖRST
    vagg.BT_VaggProperties,                   # <-- SEDAN vagg
    tak.BT_TakProperties,
    bjalklag.BT_BjälklagProperties,
    fonster.BT_FonsterProperties,
    dorr.BT_DorrProperties,
)