"""
Created: April, 2023

@author: tsalemink
"""
from opencmiss.zinc.field import Field
from opencmiss.zinc.glyph import Glyph


class AutoSegmentationScene(object):
    def __init__(self, model):
        self._model = model
        self._context = model.get_context()
        self._root_scene = model.get_root_scene()
        self._output_scene = model.get_output_scene()
        self._dimensions = model.get_dimensions()
        self._output_coordinates = model.get_output_coordinates()
        self._node_set = model.get_node_set()

        # Initialize the graphics.
        self._create_outline_graphics()
        self._iso_graphic = self._create_surface_graphics()
        self._segmentation_contour = self._create_segmentation_graphics()
        self._point_cloud = self._create_point_cloud_graphics()

    def _create_outline_graphics(self):
        field_module = self._model.get_field_module()
        finite_element_field = field_module.findFieldByName('coordinates')

        self._root_scene.beginChange()
        outline = self._root_scene.createGraphicsLines()
        outline.setCoordinateField(finite_element_field)
        outline.setName('element_outline')
        self._root_scene.endChange()

        return outline

    def _create_surface_graphics(self):
        field_module = self._model.get_field_module()
        finite_element_field = field_module.findFieldByName('coordinates')
        xi_field = field_module.findFieldByName('xi')
        scalar_field = self._model.get_scalar_field()
        image_field = self._model.get_image_field()

        material_module = self._context.getMaterialmodule()
        material = material_module.createMaterial()
        material.setName('texture_block')
        material.setTextureField(1, image_field)

        self._root_scene.beginChange()
        iso_graphic = self._root_scene.createGraphicsContours()
        iso_graphic.setCoordinateField(finite_element_field)
        iso_graphic.setMaterial(material)
        iso_graphic.setTextureCoordinateField(xi_field)
        iso_graphic.setIsoscalarField(scalar_field)
        iso_graphic.setListIsovalues([0.0])
        self._root_scene.endChange()

        return iso_graphic

    def _create_segmentation_graphics(self):
        field_module = self._model.get_field_module()
        scale_field = self._model.get_field_module().createFieldConstant(self._dimensions)
        xi_field = field_module.findFieldByName('xi')
        scaled_xi_field = xi_field * scale_field
        image_field = self._model.get_image_field()

        tessellation_module = self._context.getTessellationmodule()
        tessellation = tessellation_module.createTessellation()
        tessellation.setMinimumDivisions([256, 125, 128])

        self._root_scene.beginChange()
        segmentation_contour = self._root_scene.createGraphicsContours()
        segmentation_contour.setCoordinateField(scaled_xi_field)
        segmentation_contour.setTessellation(tessellation)
        segmentation_contour.setIsoscalarField(image_field)
        segmentation_contour.setListIsovalues([0.0])
        self._root_scene.endChange()

        return segmentation_contour

    def _create_point_cloud_graphics(self):
        self._output_scene.beginChange()
        point_cloud = self._output_scene.createGraphicsPoints()
        point_cloud.setFieldDomainType(Field.DOMAIN_TYPE_NODES)
        point_cloud.setCoordinateField(self._output_coordinates)
        attributes = point_cloud.getGraphicspointattributes()
        attributes.setGlyphShapeType(Glyph.SHAPE_TYPE_SPHERE)
        attributes.setBaseSize([min(self._dimensions) / 100])
        self._output_scene.endChange()

        return point_cloud

    def set_image_plane_visibility(self, state):
        self._iso_graphic.setVisibilityFlag(state != 0)

    def set_segmentation_visibility(self, state):
        self._segmentation_contour.setVisibilityFlag(state != 0)

    def set_point_cloud_visibility(self, state):
        self._point_cloud.setVisibilityFlag(state != 0)

    def set_slider_value(self, value):
        self._iso_graphic.setListIsovalues([value * self._dimensions[2] / 100])

    def set_segmentation_value(self, value):
        self._segmentation_contour.setListIsovalues([value / 10000.0])

    def generate_points(self):
        self.set_image_plane_visibility(0)
        self._model.generate_points()
        self.set_image_plane_visibility(1)

    def get_tessellation_divisions(self):
        return self._segmentation_contour.getTessellation().getMinimumDivisions(3)[1]

    def set_tessellation_divisions(self, divisions):
        self._segmentation_contour.getTessellation().setMinimumDivisions(divisions)
