from rpy2 import robjects
from rpy2.interactive import process_revents
from rpy2.robjects.packages import importr, data
from rpy2.robjects.vectors import IntVector, FloatVector
from rpy2.robjects.lib import grdevices

try:
    process_revents.start()
except:
    pass

base = importr('base')
lattice = importr('lattice')
datasets = importr('datasets')

rprint = robjects.globalenv.find("print")

volcano = data(datasets).fetch("volcano")["volcano"]
plot = lattice.wireframe(volcano, shade = True,
                         zlab = "value",
                         aspect = FloatVector((61.0/87, 0.4)),
                         light_source = IntVector((10,0,10)))

with grdevices.render_to_bytesio(grdevices.svg) as svg:
    rprint(plot)
process_revents.stop()

svg.getvalue() 
