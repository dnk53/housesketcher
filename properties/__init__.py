# ________________________________________________________________________________________________
# PROPERTIES PAKET
# ________________________________________________________________________________________________

from . import huvudmatt
from . import platta
from . import vagg
from . import vagg_settings
from . import tak
from . import bjalklag
from . import fonster
from . import dorr
from . import innervagg  # <-- LÄGG TILL

classes = (
    huvudmatt.BT_HuvudmåttProperties,
    platta.BT_PlattaProperties,
    vagg_settings.BT_VaggSettingsProperties,
    vagg.BT_VaggProperties,
    tak.BT_TakProperties,
    bjalklag.BT_BjälklagProperties,
    fonster.BT_FonsterProperties,
    dorr.BT_DorrProperties,
    innervagg.BT_InnervaggProperties,  # <-- LÄGG TILL
)