from rpy2.interactive import process_revents
from rpy2.robjects.packages import importr
from rpy2.robjects.vectors import IntVector
from rpy2.robjects.lib import grdevices

try:
    process_revents.start()
except:
    pass

graphics = importr("graphics")

with grdevices.render_to_bytesio(grdevices.svg) as svg:
    graphics.barplot(IntVector((1, 6, 3, 5, 4, 1)), ylab="Value")
process_revents.stop()
svg.getvalue()
