import copy

import lenstronomy.Util.util as util
import lenstronomy.Util.mask as util_maskl
import matplotlib.pyplot as plt
import numpy as np
import scipy.ndimage as ndimage
from lenstronomy.LensModel.Profiles.external_shear import ExternalShear
from mpl_toolkits.axes_grid1 import make_axes_locatable
from lenstronomy.LensModel.lens_model import LensModel
from lenstronomy.LensModel.lens_model_extensions import LensModelExtensions
import lenstronomy.Util.class_creator as class_creator
from lenstronomy.Analysis.lens_analysis import LensAnalysis
from lenstronomy.Data.coord_transforms import Coordinates
from lenstronomy.Data.imaging_data import Data


def text_description(ax, d, text, color='w', backgroundcolor='k', flipped=False):
    if flipped:
        ax.text(d - d / 40., d - d / 15., text, color=color, fontsize=15, backgroundcolor=backgroundcolor)
    else:
        ax.text(d / 40., d - d / 15., text, color=color, fontsize=15, backgroundcolor=backgroundcolor)


def scale_bar(ax, d, dist=1., text='1"', color='w', flipped=False):
    if flipped:
        p0 = d - d / 15. - dist
        p1 = d / 15.
        ax.plot([p0, p0 + dist], [p1, p1], linewidth=2, color=color)
        ax.text(p0 + dist / 2., p1 + 0.01 * d, text, fontsize=15, color=color, ha='center')
    else:
        p0 = d / 15.
        ax.plot([p0, p0 + dist], [p0, p0], linewidth=2, color=color)
        ax.text(p0 + dist / 2., p0 + 0.01 * d, text, fontsize=15, color=color, ha='center')


def coordinate_arrows(ax, d, coords, color='w', arrow_size=0.05):
    d0 = d / 8.
    p0 = d / 15.
    pt = d / 9.
    deltaPix = coords.pixel_size
    ra0, dec0 = coords.map_pix2coord((d - d0) / deltaPix, d0 / deltaPix)
    xx_, yy_ = coords.map_coord2pix(ra0, dec0)
    xx_ra, yy_ra = coords.map_coord2pix(ra0 + p0, dec0)
    xx_dec, yy_dec = coords.map_coord2pix(ra0, dec0 + p0)
    xx_ra_t, yy_ra_t = coords.map_coord2pix(ra0 + pt, dec0)
    xx_dec_t, yy_dec_t = coords.map_coord2pix(ra0, dec0 + pt)

    ax.arrow(xx_ * deltaPix, yy_ * deltaPix, (xx_ra - xx_) * deltaPix, (yy_ra - yy_) * deltaPix,
             head_width=arrow_size * d, head_length=arrow_size * d, fc=color, ec=color, linewidth=1)
    ax.text(xx_ra_t * deltaPix, yy_ra_t * deltaPix, "E", color=color, fontsize=15, ha='center')
    ax.arrow(xx_ * deltaPix, yy_ * deltaPix, (xx_dec - xx_) * deltaPix, (yy_dec - yy_) * deltaPix,
             head_width=arrow_size * d, head_length=arrow_size * d, fc
             =color, ec=color, linewidth=1)
    ax.text(xx_dec_t * deltaPix, yy_dec_t * deltaPix, "N", color=color, fontsize=15, ha='center')


def plot_line_set(ax, coords, ra_caustic_list, dec_caustic_list, color='g'):
    """

    :param coords:
    :return:
    """
    deltaPix = coords.pixel_size
    #for i in range(len(ra_caustic_list)):
    x_c, y_c = coords.map_coord2pix(ra_caustic_list, dec_caustic_list)
    ax.plot((x_c + 0.5) * (deltaPix), (y_c + 0.5) * (deltaPix), ',', color=color)
    return ax


def image_position_plot(ax, coords, ra_image, dec_image, color='w', image_name_list=None):
    """

    :param ax:
    :param coords:
    :param kwargs_else:
    :return:
    """
    deltaPix = coords.pixel_size
    if len(ra_image) > 0:
        if len(ra_image[0]) > 0:
            x_image, y_image = coords.map_coord2pix(ra_image[0], dec_image[0])
            if image_name_list is None:
                image_name_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
            for i in range(len(x_image)):
                x_ = (x_image[i] + 0.5) * deltaPix
                y_ = (y_image[i] + 0.5) * deltaPix
                ax.plot(x_, y_, 'or')
                ax.text(x_, y_, image_name_list[i], fontsize=20, color=color)
    return ax


def source_position_plot(ax, coords, kwargs_source):
    """

    :param ax:
    :param coords:
    :param kwargs_source:
    :return:
    """
    deltaPix = coords.pixel_size
    if len(kwargs_source) > 0:
        if 'center_x' in kwargs_source[0]:
            x_source, y_source = coords.map_coord2pix(kwargs_source[0]['center_x'], kwargs_source[0]['center_y'])
            ax.plot((x_source + 0.5) * deltaPix, (y_source + 0.5) * deltaPix, '*', markersize=10)
    return ax


def lens_model_plot(ax, lensModel, kwargs_lens, numPix=500, deltaPix=0.01, sourcePos_x=0, sourcePos_y=0, point_source=False, with_caustics=False):
    """
    plots a lens model (convergence) and the critical curves and caustics

    :param ax:
    :param kwargs_lens:
    :param numPix:
    :param deltaPix:
    :return:
    """
    from lenstronomy.SimulationAPI.simulations import Simulation
    simAPI = Simulation()
    data = simAPI.data_configure(numPix, deltaPix)
    _frame_size = numPix * deltaPix
    _coords = data._coords
    x_grid, y_grid = data.coordinates
    lensModelExt = LensModelExtensions(lensModel)

    #ra_crit_list, dec_crit_list, ra_caustic_list, dec_caustic_list = lensModelExt.critical_curve_caustics(
    #    kwargs_lens, compute_window=_frame_size, grid_scale=deltaPix/2.)
    x_grid1d = util.image2array(x_grid)
    y_grid1d = util.image2array(y_grid)
    kappa_result = lensModel.kappa(x_grid1d, y_grid1d, kwargs_lens)
    kappa_result = util.array2image(kappa_result)
    im = ax.matshow(np.log10(kappa_result), origin='lower',
                    extent=[0, _frame_size, 0, _frame_size], cmap='Greys', vmin=-1, vmax=1) #, cmap=self._cmap, vmin=v_min, vmax=v_max)
    if with_caustics is True:
        ra_crit_list, dec_crit_list = lensModelExt.critical_curve_tiling(kwargs_lens, compute_window=_frame_size,
                                                                         start_scale=deltaPix, max_order=10)
        ra_caustic_list, dec_caustic_list = lensModel.ray_shooting(ra_crit_list, dec_crit_list, kwargs_lens)
        plot_line_set(ax, _coords, ra_caustic_list, dec_caustic_list, color='g')
        plot_line_set(ax, _coords, ra_crit_list, dec_crit_list, color='r')
    if point_source:
        from lenstronomy.LensModel.Solver.lens_equation_solver import LensEquationSolver
        solver = LensEquationSolver(lensModel)
        theta_x, theta_y = solver.image_position_from_source(sourcePos_x, sourcePos_y, kwargs_lens)
        mag_images = lensModel.magnification(theta_x, theta_y, kwargs_lens)
        x_image, y_image = _coords.map_coord2pix(theta_x, theta_y)
        abc_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']
        for i in range(len(x_image)):
            x_ = (x_image[i] + 0.5) * deltaPix
            y_ = (y_image[i] + 0.5) * deltaPix
            ax.plot(x_, y_, 'dk', markersize=4*(1 + np.log(np.abs(mag_images[i]))), alpha=0.5)
            ax.text(x_, y_, abc_list[i], fontsize=20, color='k')
        x_source, y_source = _coords.map_coord2pix(sourcePos_x, sourcePos_y)
        ax.plot((x_source + 0.5) * deltaPix, (y_source + 0.5) * deltaPix, '*k', markersize=10)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.autoscale(False)
    #image_position_plot(ax, _coords, self._kwargs_else)
    #source_position_plot(ax, self._coords, self._kwargs_source)
    return ax


class LensModelPlot(object):
    """
    class that manages the summary plots of a lens model
    """
    def __init__(self, kwargs_data, kwargs_psf, kwargs_numerics, kwargs_model, kwargs_lens, kwargs_source,
                 kwargs_lens_light, kwargs_ps, arrow_size=0.02, cmap_string="gist_heat"):
        """

        :param kwargs_options:
        :param kwargs_data:
        :param arrow_size:
        :param cmap_string:
        """
        self._kwargs_data = kwargs_data
        if isinstance(cmap_string, str) or isinstance(cmap_string, unicode):
            cmap = plt.get_cmap(cmap_string)
        else:
            cmap = cmap_string
        cmap.set_bad(color='k', alpha=1.)
        cmap.set_under('k')
        self._cmap = cmap
        self._arrow_size = arrow_size
        data = Data(kwargs_data)
        self._coords = data._coords
        nx, ny = np.shape(kwargs_data['image_data'])
        Mpix2coord = kwargs_data['transform_pix2angle']
        self._Mpix2coord = Mpix2coord

        self._deltaPix = self._coords.pixel_size
        self._frame_size = self._deltaPix * nx

        x_grid, y_grid = data.coordinates
        self._x_grid = util.image2array(x_grid)
        self._y_grid = util.image2array(y_grid)

        self._imageModel = class_creator.create_image_model(kwargs_data, kwargs_psf, kwargs_numerics, kwargs_model)
        self._analysis = LensAnalysis(kwargs_model)
        self._lensModel = LensModel(lens_model_list=kwargs_model.get('lens_model_list', []),
                                 z_source=kwargs_model.get('z_source', None),
                                 redshift_list=kwargs_model.get('redshift_list', None),
                                 multi_plane=kwargs_model.get('multi_plane', False))
        self._lensModelExt = LensModelExtensions(self._lensModel)
        model, error_map, cov_param, param = self._imageModel.image_linear_solve(kwargs_lens, kwargs_source,
                                                                                 kwargs_lens_light, kwargs_ps, inv_bool=True)
        self._kwargs_lens = kwargs_lens
        self._kwargs_source = kwargs_source
        self._kwargs_lens_light = kwargs_lens_light
        self._kwargs_else = kwargs_ps
        self._model = model
        self._data = kwargs_data['image_data']
        self._cov_param = cov_param
        self._norm_residuals = self._imageModel.reduced_residuals(model, error_map=error_map)
        self._reduced_x2 = self._imageModel.reduced_chi2(model, error_map=error_map)
        log_model = np.log10(model)
        log_model[np.isnan(log_model)] = -5
        self._v_min_default = max(np.min(log_model), -5)
        self._v_max_default = min(np.max(log_model), 10)
        print("reduced chi^2 = ", self._reduced_x2)

    def _critical_curves(self):
        if not hasattr(self, '_ra_crit_list') or not hasattr(self, '_dec_crit_list'):
            self._ra_crit_list, self._dec_crit_list = self._lensModelExt.critical_curve_tiling(self._kwargs_lens,
                                                                                        compute_window=self._frame_size,
                                                                                        start_scale=self._deltaPix / 5.,
                                                                                        max_order=10)
        return self._ra_crit_list, self._dec_crit_list

    def _caustics(self):
        if not hasattr(self, '_ra_caustic_list') or not hasattr(self, '_dec_caustic_list'):
            ra_crit_list, dec_crit_list = self._critical_curves()
            self._ra_caustic_list, self._dec_caustic_list = self._lensModel.ray_shooting(ra_crit_list,
                                                                                     dec_crit_list, self._kwargs_lens)
        return self._ra_caustic_list, self._dec_caustic_list

    def data_plot(self, ax, v_min=None, v_max=None, text='Observed'):
        """

        :param ax:
        :return:
        """
        if v_min is None:
            v_min = self._v_min_default
        if v_max is None:
            v_max = self._v_max_default
        im = ax.matshow(np.log10(self._data), origin='lower',
                        extent=[0, self._frame_size, 0, self._frame_size], cmap=self._cmap, vmin=v_min, vmax=v_max)  # , vmin=0, vmax=2

        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.autoscale(False)

        scale_bar(ax, self._frame_size, dist=1, text='1"')
        text_description(ax, self._frame_size, text=text, color="w", backgroundcolor='k')
        coordinate_arrows(ax, self._frame_size, self._coords, arrow_size=self._arrow_size)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cb = plt.colorbar(im, cax=cax, orientation='vertical')
        cb.set_label(r'log$_{10}$ flux', fontsize=15)
        return ax

    def model_plot(self, ax, v_min=None, v_max=None, image_names=False):
        """

        :param ax:
        :param model:
        :param v_min:
        :param v_max:
        :return:
        """
        if v_min is None:
            v_min = self._v_min_default
        if v_max is None:
            v_max = self._v_max_default
        im = ax.matshow(np.log10(self._model), origin='lower', vmin=v_min, vmax=v_max,
                        extent=[0, self._frame_size, 0, self._frame_size], cmap=self._cmap)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.autoscale(False)
        scale_bar(ax, self._frame_size, dist=1, text='1"')
        text_description(ax, self._frame_size, text="Reconstructed", color="w", backgroundcolor='k')
        coordinate_arrows(ax, self._frame_size, self._coords, arrow_size=self._arrow_size)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cb = plt.colorbar(im, cax=cax)
        cb.set_label(r'log$_{10}$ flux', fontsize=15)

        #plot_line_set(ax, self._coords, self._ra_caustic_list, self._dec_caustic_list, color='b')
        #plot_line_set(ax, self._coords, self._ra_crit_list, self._dec_crit_list, color='r')
        if image_names is True:
            ra_image, dec_image = self._imageModel.image_positions(self._kwargs_else, self._kwargs_lens)
            image_position_plot(ax, self._coords, ra_image, dec_image)
        #source_position_plot(ax, self._coords, self._kwargs_source)

    def convergence_plot(self, ax, v_min=None, v_max=None):
        """

        :param x_grid:
        :param y_grid:
        :param kwargs_lens:
        :param kwargs_else:
        :return:
        """
        kappa_result = util.array2image(self._lensModel.kappa(self._x_grid, self._y_grid, self._kwargs_lens))
        im = ax.matshow(np.log10(kappa_result), origin='lower',
                        extent=[0, self._frame_size, 0, self._frame_size], cmap=self._cmap, vmin=v_min, vmax=v_max)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.autoscale(False)
        scale_bar(ax, self._frame_size, dist=1, text='1"', color='w')
        coordinate_arrows(ax, self._frame_size, self._coords, color='w', arrow_size=self._arrow_size)
        text_description(ax, self._frame_size, text="Convergence", color="w", backgroundcolor='k', flipped=False)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cb = plt.colorbar(im, cax=cax)
        cb.set_label(r'log$_{10}$ $\kappa$', fontsize=15)
        return ax

    def normalized_residual_plot(self, ax, v_min=-6, v_max=6, **kwargs):
        """

        :param ax:
        :param v_min:
        :param v_max:
        :param kwargs: kwargs to send to matplotlib.pyplot.matshow()
        :return:
        """
        if not 'cmap' in kwargs:
            kwargs['cmap'] = 'bwr'
        im = ax.matshow(self._norm_residuals, vmin=v_min, vmax=v_max,
                        extent=[0, self._frame_size, 0, self._frame_size], origin='lower', **kwargs)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.autoscale(False)
        scale_bar(ax, self._frame_size, dist=1, text='1"', color='k')
        text_description(ax, self._frame_size, text="Normalized Residuals", color="k", backgroundcolor='w')
        coordinate_arrows(ax, self._frame_size, self._coords, color='k', arrow_size=self._arrow_size)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cb = plt.colorbar(im, cax=cax)
        cb.set_label(r'(f$_{model}$-f$_{data}$)/$\sigma$', fontsize=15)
        return ax

    def absolute_residual_plot(self, ax, v_min=-1, v_max=1):
        """

        :param ax:
        :param residuals:
        :return:
        """
        im = ax.matshow(self._model - self._data, vmin=v_min, vmax=v_max,
                        extent=[0, self._frame_size, 0, self._frame_size], cmap='bwr', origin='lower')
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.autoscale(False)
        scale_bar(ax, self._frame_size, dist=1, text='1"', color='k')
        text_description(ax, self._frame_size, text="Residuals", color="k", backgroundcolor='w')
        coordinate_arrows(ax, self._frame_size, self._coords, color='k', arrow_size=self._arrow_size)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cb = plt.colorbar(im, cax=cax)
        cb.set_label(r'(f$_{model}$-f$_{data}$)', fontsize=15)
        return ax

    def source_plot(self, ax, numPix, deltaPix_source, source_sigma=0.001, convolution=False, v_min=None, v_max=None, with_caustics=False):
        """

        :param ax:
        :param coords_source:
        :param source:
        :return:
        """
        if v_min is None:
            v_min = self._v_min_default
        if v_max is None:
            v_max = self._v_max_default
        d_s = numPix * deltaPix_source
        x_grid_source, y_grid_source = util.make_grid_transformed(numPix,
                                                                  self._Mpix2coord * deltaPix_source / self._deltaPix)
        if len(self._kwargs_source) > 0:
            x_center = self._kwargs_source[0]['center_x']
            y_center = self._kwargs_source[0]['center_y']
            x_grid_source += x_center
            y_grid_source += y_center
        coords_source = Coordinates(self._Mpix2coord * deltaPix_source / self._deltaPix, ra_at_xy_0=x_grid_source[0],
                                    dec_at_xy_0=y_grid_source[0])

        source = self._imageModel.SourceModel.surface_brightness(x_grid_source, y_grid_source, self._kwargs_source)
        source = util.array2image(source)
        if convolution:
            source = ndimage.filters.gaussian_filter(source, sigma=source_sigma / deltaPix_source, mode='nearest',
                                                      truncate=20)

        im = ax.matshow(np.log10(source), origin='lower', extent=[0, d_s, 0, d_s],
                        cmap=self._cmap, vmin=v_min, vmax=v_max)  # source
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.autoscale(False)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cb = plt.colorbar(im, cax=cax)
        cb.set_label(r'log$_{10}$ flux', fontsize=15)
        if with_caustics:
            ra_caustic_list, dec_caustic_list = self._caustics()
            plot_line_set(ax, coords_source, ra_caustic_list, dec_caustic_list, color='b')
        scale_bar(ax, d_s, dist=0.1, text='0.1"', color='w', flipped=False)
        coordinate_arrows(ax, d_s, coords_source, arrow_size=self._arrow_size, color='w')
        text_description(ax, d_s, text="Reconstructed source", color="w", backgroundcolor='k', flipped=False)
        source_position_plot(ax, coords_source, self._kwargs_source)
        return ax

    def error_map_source_plot(self, ax, numPix, deltaPix_source, v_min=None, v_max=None, with_caustics=False):
        x_grid_source, y_grid_source = util.make_grid_transformed(numPix,
                                                                  self._Mpix2coord * deltaPix_source / self._deltaPix)
        x_center = self._kwargs_source[0]['center_x']
        y_center = self._kwargs_source[0]['center_y']
        x_grid_source += x_center
        y_grid_source += y_center
        coords_source = Coordinates(self._Mpix2coord * deltaPix_source / self._deltaPix, ra_at_xy_0=x_grid_source[0],
                                    dec_at_xy_0=y_grid_source[0])
        error_map_source = self._analysis.error_map_source(self._kwargs_source, x_grid_source, y_grid_source, self._cov_param)
        error_map_source = util.array2image(error_map_source)
        d_s = numPix * deltaPix_source
        im = ax.matshow(error_map_source, origin='lower', extent=[0, d_s, 0, d_s],
                        cmap=self._cmap, vmin=v_min, vmax=v_max)  # source
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.autoscale(False)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cb = plt.colorbar(im, cax=cax)
        cb.set_label(r'error variance', fontsize=15)
        if with_caustics:
            ra_caustic_list, dec_caustic_list = self._caustics()
            plot_line_set(ax, coords_source, ra_caustic_list, dec_caustic_list, color='b')
        scale_bar(ax, d_s, dist=0.1, text='0.1"', color='w', flipped=False)
        coordinate_arrows(ax, d_s, coords_source, arrow_size=self._arrow_size, color='w')
        text_description(ax, d_s, text="Error map in source", color="w", backgroundcolor='k', flipped=False)
        source_position_plot(ax, coords_source, self._kwargs_source)
        return ax

    def magnification_plot(self, ax, v_min=-10, v_max=10, with_caustics=False, image_name_list=None, **kwargs):
        """

        :param ax:
        :param v_min:
        :param v_max:
        :param with_caustics:
        :param kwargs: kwargs to send to matplotlib.pyplot.matshow()
        :return:
        """
        if not 'cmap' in kwargs:
            kwargs['cmap'] = self._cmap
        if not 'alpha' in kwargs:
            kwargs['alpha'] = 0.5
        mag_result = util.array2image(self._lensModel.magnification(self._x_grid, self._y_grid, self._kwargs_lens))
        im = ax.matshow(mag_result, origin='lower', extent=[0, self._frame_size, 0, self._frame_size],
                        vmin=v_min, vmax=v_max, **kwargs)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.autoscale(False)
        scale_bar(ax, self._frame_size, dist=1, text='1"', color='k')
        coordinate_arrows(ax, self._frame_size, self._coords, color='k', arrow_size=self._arrow_size)
        text_description(ax, self._frame_size, text="Magnification model", color="k", backgroundcolor='w')
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cb = plt.colorbar(im, cax=cax)
        cb.set_label(r'det(A$^{-1}$)', fontsize=15)
        if with_caustics:
            ra_crit_list, dec_crit_list = self._critical_curves()
            ra_caustic_list, dec_caustic_list = self._caustics()
            plot_line_set(ax, self._coords, ra_caustic_list, dec_caustic_list, color='b')
            plot_line_set(ax, self._coords, ra_crit_list, dec_crit_list, color='r')
        ra_image, dec_image = self._imageModel.image_positions(self._kwargs_else, self._kwargs_lens)
        image_position_plot(ax, self._coords, ra_image, dec_image, color='k', image_name_list=image_name_list)
        source_position_plot(ax, self._coords, self._kwargs_source)
        return ax

    def deflection_plot(self, ax, v_min=None, v_max=None, axis=0, with_caustics=False, image_name_list=None):
        """

        :param kwargs_lens:
        :param kwargs_else:
        :return:
        """

        alpha1, alpha2 = self._lensModel.alpha(self._x_grid, self._y_grid, self._kwargs_lens)
        alpha1 = util.array2image(alpha1)
        alpha2 = util.array2image(alpha2)
        if axis == 0:
            alpha = alpha1
        else:
            alpha = alpha2
        im = ax.matshow(alpha, origin='lower', extent=[0, self._frame_size, 0, self._frame_size],
                        vmin=v_min, vmax=v_max, cmap=self._cmap, alpha=0.5)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.autoscale(False)
        scale_bar(ax, self._frame_size, dist=1, text='1"', color='k')
        coordinate_arrows(ax, self._frame_size, self._coords, color='k', arrow_size=self._arrow_size)
        text_description(ax, self._frame_size, text="Deflection model", color="k", backgroundcolor='w')
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cb = plt.colorbar(im, cax=cax)
        cb.set_label(r'arcsec', fontsize=15)
        if with_caustics:
            ra_crit_list, dec_crit_list = self._critical_curves()
            ra_caustic_list, dec_caustic_list = self._caustics()
            plot_line_set(ax, self._coords, ra_caustic_list, dec_caustic_list, color='b')
            plot_line_set(ax, self._coords, ra_crit_list, dec_crit_list, color='r')
        ra_image, dec_image = self._imageModel.image_positions(self._kwargs_else, self._kwargs_lens)
        image_position_plot(ax, self._coords, ra_image, dec_image, image_name_list=image_name_list)
        source_position_plot(ax, self._coords, self._kwargs_source)
        return ax

    def decomposition_plot(self, ax, text='Reconstructed', v_min=None, v_max=None, unconvolved=False, point_source_add=False, source_add=False, lens_light_add=False, **kwargs):
        """

        :param ax:
        :param text:
        :param v_min:
        :param v_max:
        :param unconvolved:
        :param point_source_add:
        :param source_add:
        :param lens_light_add:
        :param kwargs: kwargs to send matplotlib.pyplot.matshow()
        :return:
        """
        model = self._imageModel.image(self._kwargs_lens, self._kwargs_source, self._kwargs_lens_light,
                                          self._kwargs_else, unconvolved=unconvolved, source_add=source_add,
                                          lens_light_add=lens_light_add, point_source_add=point_source_add)
        if v_min is None:
            v_min = self._v_min_default
        if v_max is None:
            v_max = self._v_max_default
        if not 'cmap' in kwargs:
            kwargs['cmap'] = self._cmap
        im = ax.matshow(np.log10(model), origin='lower', vmin=v_min, vmax=v_max,
                        extent=[0, self._frame_size, 0, self._frame_size], **kwargs)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.autoscale(False)
        scale_bar(ax, self._frame_size, dist=1, text='1"')
        text_description(ax, self._frame_size, text=text, color="w", backgroundcolor='k')
        coordinate_arrows(ax, self._frame_size, self._coords, arrow_size=self._arrow_size)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cb = plt.colorbar(im, cax=cax)
        cb.set_label(r'log$_{10}$ flux', fontsize=15)
        return ax

    def subtract_from_data_plot(self, ax, text='Subtracted', v_min=None, v_max=None, point_source_add=False, source_add=False, lens_light_add=False):
        model = self._imageModel.image(self._kwargs_lens, self._kwargs_source, self._kwargs_lens_light,
                                          self._kwargs_else, unconvolved=False, source_add=source_add,
                                          lens_light_add=lens_light_add, point_source_add=point_source_add)
        if v_min is None:
            v_min = self._v_min_default
        if v_max is None:
            v_max = self._v_max_default
        im = ax.matshow(np.log10(self._data - model), origin='lower', vmin=v_min, vmax=v_max,
                        extent=[0, self._frame_size, 0, self._frame_size], cmap=self._cmap)
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.autoscale(False)
        scale_bar(ax, self._frame_size, dist=1, text='1"')
        text_description(ax, self._frame_size, text=text, color="w", backgroundcolor='k')
        coordinate_arrows(ax, self._frame_size, self._coords, arrow_size=self._arrow_size)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cb = plt.colorbar(im, cax=cax)
        cb.set_label(r'log$_{10}$ flux', fontsize=15)
        return ax


def plot_chain(chain, param_list):
    X2_list, pos_list, vel_list, _ = chain

    f, axes = plt.subplots(1, 3, figsize=(18, 6))
    ax = axes[0]
    ax.plot(np.log10(-np.array(X2_list)))
    ax.set_title('-logL')

    ax = axes[1]
    pos = np.array(pos_list)
    vel = np.array(vel_list)
    n_iter = len(pos)
    plt.figure()
    for i in range(0,len(pos[0])):
        ax.plot((pos[:,i]-pos[n_iter-1,i]),label=param_list[i])
    ax.set_title('particle position')
    ax.legend()

    ax = axes[2]
    for i in range(0,len(vel[0])):
        ax.plot(vel[:,i], label=param_list[i])
    ax.set_title('param velocity')
    ax.legend()
    return f, axes


def plot_mcmc_behaviour(ax, samples_mcmc, param_mcmc, dist_mcmc, num_average=100):
    """
    plots the MCMC behaviour and looks for convergence of the chain
    :param samples_mcmc: parameters sampled 2d numpy array
    :param param_mcmc: list of parameters
    :param dist_mcmc: log likelihood of the chain
    :param num_average: number of samples to average (should coincide with the number of samples in the emcee process)
    :return:
    """
    num_samples = len(samples_mcmc[:, 0])
    num_average = int(num_average)
    n_points = int((num_samples - num_samples % num_average) / num_average)
    for i, param_name in enumerate(param_mcmc):
        samples = samples_mcmc[:, i]
        samples_averaged = np.average(samples[:int(n_points * num_average)].reshape(n_points, num_average), axis=1)
        end_point = np.mean(samples_averaged)
        samples_renormed = (samples_averaged - end_point) / np.std(samples_averaged)
        ax.plot(samples_renormed, label=param_name)

    dist_averaged = -np.max(dist_mcmc[:int(n_points * num_average)].reshape(n_points, num_average), axis=1)
    dist_normed = (dist_averaged - np.max(dist_averaged)) / (np.max(dist_averaged) - np.min(dist_averaged))
    ax.plot(dist_normed, label="logL", color='k', linewidth=2)
    ax.legend()
    return ax


def ext_shear_direction(data_class, lens_model_class, kwargs_lens, strength_multiply=10):
    """

    :param kwargs_data:
    :param kwargs_psf:
    :param kwargs_options:
    :param lens_result:
    :param source_result:
    :param lens_light_result:
    :param else_result:
    :return:
    """
    x_grid, y_grid = data_class.coordinates
    x_grid = util.image2array(x_grid)
    y_grid = util.image2array(y_grid)
    shear = ExternalShear()

    f_x_shear, f_y_shear = 0, 0
    for i, lens_model in enumerate(lens_model_class.lens_model_list):
        if lens_model == 'SHEAR':
            kwargs = kwargs_lens[i]
            f_x_shear, f_y_shear = shear.derivatives(x_grid, y_grid, e1=kwargs['e1'] * strength_multiply,
                                                         e2=kwargs['e2'] * strength_multiply)
    x_shear = x_grid - f_x_shear
    y_shear = y_grid - f_y_shear

    f_x_foreground, f_y_foreground = 0, 0
    for i, lens_model in enumerate(lens_model_class.lens_model_list):
        if lens_model == 'FOREGROUND_SHEAR':
            kwargs = kwargs_lens[i]
            f_x_foreground, f_y_foreground = shear.derivatives(x_grid, y_grid, e1=kwargs['e1'] * strength_multiply,
                                                     e2=kwargs['e2'] * strength_multiply)
    x_foreground = x_grid - f_x_foreground
    y_foreground = y_grid - f_y_foreground

    center_x = np.mean(x_grid)
    center_y = np.mean(y_grid)
    radius = (np.max(x_grid) - np.min(x_grid))/4
    circle_shear = util_maskl.mask_sphere(x_shear, y_shear, center_x, center_y, radius)
    circle_foreground = util_maskl.mask_sphere(x_foreground, y_foreground, center_x, center_y, radius)
    f, ax = plt.subplots(1, 1, figsize=(16, 8))
    im = ax.matshow(np.log10(data_class.data), origin='lower', alpha=0.5)
    im = ax.matshow(util.array2image(circle_shear), origin='lower', alpha=0.5, cmap="jet")
    im = ax.matshow(util.array2image(circle_foreground), origin='lower', alpha=0.5)
    #f.show()
    return f, ax


def psf_iteration_compare(kwargs_psf, **kwargs):
    """

    :param kwargs_psf:
    :param kwargs: kwargs to send to matplotlib.pyplot.matshow()
    :return:
    """
    psf_out = kwargs_psf['kernel_point_source']
    psf_in = kwargs_psf['kernel_point_source_init']
    n_kernel = len(psf_in)
    delta_x = n_kernel/20.
    delta_y = n_kernel/10.

    if not 'cmap' in kwargs:
        kwargs['cmap'] = 'seismic'

    f, axes = plt.subplots(1, 3, figsize=(15, 5))
    ax = axes[0]
    im = ax.matshow(np.log10(psf_in), origin='lower', **kwargs)
    v_min, v_max = im.get_clim()
    if not 'vmin' in kwargs:
        kwargs['vmin'] = v_min
    if not 'vmax' in kwargs:
        kwargs['vmax'] = v_max
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    plt.colorbar(im, cax=cax)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.text(delta_x, n_kernel-delta_y, "stacked stars", color="k", fontsize=20, backgroundcolor='w')

    ax = axes[1]
    im = ax.matshow(np.log10(psf_out), origin='lower', **kwargs)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    plt.colorbar(im, cax=cax)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.text(delta_x, n_kernel-delta_y, "iterative reconstruction", color="k", fontsize=20, backgroundcolor='w')

    ax = axes[2]
    kwargs_new = copy.deepcopy(kwargs)
    try:
        del kwargs_new['vmin']
        del kwargs_new['vmax']
    except:
        pass
    im = ax.matshow(psf_out-psf_in, origin='lower', vmin=-10**-3, vmax=10**-3, **kwargs_new)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    plt.colorbar(im, cax=cax)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.text(delta_x, n_kernel-delta_y, "difference", color="k", fontsize=20, backgroundcolor='w')
    f.tight_layout()
    return f, axes