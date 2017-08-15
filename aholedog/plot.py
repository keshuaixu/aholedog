import numpy as np
import time
from bokeh.layouts import gridplot, column, row
from bokeh.models import Span
from numpy import pi

from bokeh.client import push_session
from bokeh.driving import cosine
from bokeh.plotting import figure, curdoc
from threading import Thread
from multiprocessing import Process

from aholedog.gait import GaitGenerator


class GaitPlotter:
    def __init__(self, gaitgen: GaitGenerator):
        self.g = gaitgen
        # self.p = figure()
        self.xyz_figs = []
        self.theta_figs = []
        self.xyz_lines = []
        self.theta_lines = []
        self.spans = []
        for i in range(12):
            fig = figure(plot_width=500, plot_height=100, title=None)
            line = fig.line(range(gaitgen.combined_cycle.shape[1]), gaitgen.combined_cycle[i, :])
            self.xyz_lines.append(line)
            self.xyz_figs.append(fig)

            fig_theta = figure(plot_width=500, plot_height=100, title=None)
            line_theta = fig_theta.line(range(gaitgen.raw_motor_position.shape[1]), gaitgen.motor_position[i, :])
            self.theta_lines.append(line_theta)
            self.theta_figs.append(fig_theta)

            sp = Span(location=0,
                      dimension='height', line_color='green',
                      line_dash='dashed', line_width=1)
            fig.add_layout(sp)

            sp2 = Span(location=0,
                       dimension='height', line_color='green',
                       line_dash='dashed', line_width=1)
            fig_theta.add_layout(sp2)

            self.spans.append(sp)
            self.spans.append(sp2)

        curdoc().add_periodic_callback(self.update, 10)
        session = push_session(curdoc())
        self.p = gridplot([list(i) for i in zip(self.xyz_figs, self.theta_figs)], webgl=True)
        # self.p = row(column(self.xyz_figs), column(self.theta_figs))
        session.show(self.p)  # open the document in a browser

        # time.sleep(20)
        Thread(target=session.loop_until_closed).start()
        # Process(target=session.loop_until_closed).start()

    def update(self):
        for i in range(12):
            self.xyz_lines[i].data_source.data["x"] = range(self.g.combined_cycle.shape[1])
            self.xyz_lines[i].data_source.data["y"] = self.g.combined_cycle[i, :]
            self.theta_lines[i].data_source.data["x"] = range(self.g.raw_motor_position.shape[1])
            self.theta_lines[i].data_source.data["y"] = self.g.motor_position[i, :]

        for i in range(24):
            self.spans[i].location = self.g.current_cycle_t


#
#             # x = np.linspace(0, 4*pi, 80)
#             # y = np.sin(x)
#             #
#             # p = figure()
#             # r1 = p.line([0, 4*pi], [-1, 1], color="firebrick")
#             # r2 = p.line(x, y, color="navy", line_width=4)
#
#             x = list(range(11))
#             y0 = x
#             y1 = [10 - xx for xx in x]
#             y2 = [abs(xx - 5) for xx in x]
#
#             # create a new plot
#             s1 = figure(plot_width=250, plot_height=250, title=None)
#             a = s1.line(x, y0, color="navy", alpha=0.5)
#
#             # create a new plot and share both ranges
#             s2 = figure(plot_width=250, plot_height=250, x_range=s1.x_range, y_range=s1.y_range, title=None)
#             s2.triangle(x, y1, size=10, color="firebrick", alpha=0.5)
#
#             # create a new plot and share only one range
#             s3 = figure(plot_width=250, plot_height=250, x_range=s1.x_range, title=None)
#             s3.square(x, y2, size=10, color="olive", alpha=0.5)
#
#             p = gridplot([[s1, s2, s3]], toolbar_location=None)
#
#             # open a session to keep our local document in sync with server
#             session = push_session(curdoc()) \
#
#                       @ cosine(w=0.03)
#
#
# def update(step):
#     # updating a single column of the the *same length* is OK
#     # a.data_source.data["y"] = y0 * step
#     a.glyph.line_alpha = 1 - 0.8 * abs(step)


# curdoc().add_periodic_callback(update, 50)
#
# session.show(p)  # open the document in a browser
#
# # time.sleep(20)
# Thread(target=session.loop_until_closed).start()
# session.loop_until_closed() # run forever
time.sleep(20)
