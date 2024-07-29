import bpy
import bmesh
from bmesh.types import BMVert, BMEdge
import mathutils
from datetime import datetime
from mathutils import Matrix, Vector
from typing import cast


def print(*args):
    print_result = [str(item) for item in args]
    with open("/mnt/novaera/Python/blender_scripts/edit_tools/logs.log", "a") as f:
        now = datetime.now().strftime("%H:%M:%S")

        f.write(f"[{now}] {' '.join(print_result)}\n")


class EdgeProjector:
    @staticmethod
    def view_transform():
        areas = [
            area for area in bpy.context.window.screen.areas if area.type == "VIEW_3D"
        ]

        with bpy.context.temp_override(area=areas[0]):
            view3d = bpy.context.space_data
            view_matrix = cast(Matrix, view3d.region_3d.view_matrix)  # type: ignore
            view_matrix = view_matrix.inverted()

            return view_matrix

    @staticmethod
    def transform_position(vert: BMVert, view_normal: Vector):
        position = vert.co
        return position - position.project(view_normal)

    @staticmethod
    def transform_vert(vert: BMVert, view_normal: Vector):
        position = vert.co
        vert.co = position - position.project(view_normal)

    @staticmethod
    def calculate_percentage_of_edge(
        edge: Vector, point: Vector, original_edge: BMEdge
    ) -> Vector:
        factor = point.length / edge.length
        original_edge_vector = original_edge.verts[1].co - original_edge.verts[0].co
        return (original_edge_vector * factor) + original_edge.verts[0].co

    def execute(self):
        view_matrix = self.view_transform()

        view_normal = Vector((0, 0, 1))
        view_normal.rotate(view_matrix)

        me = ob.data if (ob := bpy.context.object) else None

        if not isinstance(me, bpy.types.Mesh):
            raise Exception("No Mesh Data")

        bm = bmesh.from_edit_mesh(me)

        edges: list[BMEdge] = []
        for edge in bm.edges:
            if edge.select:
                edges.append(edge)

        assert len(edges) == 2

        verts = [
            self.transform_position(vert, view_normal)
            for edge in edges
            for vert in edge.verts
        ]

        intersection, distance = mathutils.geometry.intersect_line_line(
            verts[0], verts[1], verts[2], verts[3]
        )

        for i in range(2):
            point = self.calculate_percentage_of_edge(
                verts[(i * 2) + 1] - verts[i], intersection - verts[i * 2], edges[i]
            )

            new_vert = bm.verts.new(point)
            new_vert.select_set(True)

        bmesh.update_edit_mesh(me)
        bm.free()


e = EdgeProjector()
e.execute()
