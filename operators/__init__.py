# ________________________________________________________________________________________________
# OPERATORS PAKET
# ________________________________________________________________________________________________

from . import generera_hus
from . import generera_platta
from . import generera_vagg
from . import generera_tak
from . import generera_bjalklag
from . import generera_fonster
from . import generera_dorr
from . import generera_innervagg
from . import placera_komponent
from . import meny_hantering

classes = (
    generera_hus.MESH_OT_bt_skapa_hus,
    generera_platta.MESH_OT_bt_skapa_platta,
    generera_vagg.MESH_OT_bt_skapa_vagg,
    generera_tak.MESH_OT_bt_skapa_tak,
    generera_bjalklag.MESH_OT_bt_skapa_bjalklag,
    generera_fonster.MESH_OT_bt_skapa_fonster,
    generera_dorr.MESH_OT_bt_skapa_dorr,
    generera_innervagg.MESH_OT_bt_skapa_innervagg,
    placera_komponent.MESH_OT_bt_placera_komponent,
    meny_hantering.MESH_OT_bt_dolj_alla_menyer,
    meny_hantering.MESH_OT_bt_uppdatera_mallar,
)