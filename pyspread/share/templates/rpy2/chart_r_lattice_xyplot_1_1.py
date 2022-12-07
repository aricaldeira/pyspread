from rpy2 import robjects
from rpy2.interactive import process_revents
from rpy2.robjects import Formula
from rpy2.robjects.packages import importr, data
from rpy2.robjects.lib import grdevices

try:
    process_revents.start()
except:
    pass

base = importr('base')
lattice = importr('lattice')
datasets = importr('datasets')

rprint = robjects.globalenv.find("print")

mtcars = data(datasets).fetch('mtcars')['mtcars']
formula = Formula('mpg ~ wt')
formula.getenvironment()['mpg'] = mtcars.rx2('mpg')
formula.getenvironment()['wt'] = mtcars.rx2('wt')
plot = lattice.xyplot(formula, type=base.c("p"), groups=mtcars.rx2('cyl'))

with grdevices.render_to_bytesio(grdevices.svg) as svg:
    rprint(plot)
process_revents.stop()

svg.getvalue() 
