import random
from PIL import Image, ImageDraw
import math

class GlyphGenerator:
    def __init__(self, seed, style="geometric", size=512):
        self.seed = seed
        self.style = style
        self.size = size
        self.grid_size = 4
        self.cell_size = size // self.grid_size
        
    def generate_glyph(self, char_id, complexity=5):
        random.seed(f"{self.seed}_{char_id}")
        
        img = Image.new('RGBA', (self.size, self.size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        primitives_count = random.randint(max(2, complexity - 2), complexity + 2)
        
        symmetry = random.choice(['none', 'vertical', 'horizontal', 'both'])
        
        primitives = []
        for _ in range(primitives_count):
            if self.style == "geometric":
                primitives.append(self._generate_geometric_primitive())
            elif self.style == "curvilinear":
                primitives.append(self._generate_curvilinear_primitive())
            elif self.style == "angular":
                primitives.append(self._generate_angular_primitive())
            else:
                primitives.append(self._generate_mixed_primitive())
        
        for primitive in primitives:
            self._draw_primitive(draw, primitive, symmetry)
        
        return img
    
    def _generate_geometric_primitive(self):
        prim_type = random.choice(['line', 'circle', 'triangle'])
        
        if prim_type == 'line':
            x1 = random.randint(0, self.grid_size - 1) * self.cell_size + self.cell_size // 2
            y1 = random.randint(0, self.grid_size - 1) * self.cell_size + self.cell_size // 2
            x2 = random.randint(0, self.grid_size - 1) * self.cell_size + self.cell_size // 2
            y2 = random.randint(0, self.grid_size - 1) * self.cell_size + self.cell_size // 2
            return {'type': 'line', 'coords': [(x1, y1), (x2, y2)], 'width': random.randint(8, 16)}
        
        elif prim_type == 'circle':
            cx = random.randint(1, self.grid_size - 2) * self.cell_size + self.cell_size // 2
            cy = random.randint(1, self.grid_size - 2) * self.cell_size + self.cell_size // 2
            radius = random.randint(self.cell_size // 3, self.cell_size)
            return {'type': 'circle', 'center': (cx, cy), 'radius': radius, 'width': random.randint(8, 16)}
        
        else:
            points = []
            for _ in range(3):
                x = random.randint(0, self.grid_size - 1) * self.cell_size + self.cell_size // 2
                y = random.randint(0, self.grid_size - 1) * self.cell_size + self.cell_size // 2
                points.append((x, y))
            return {'type': 'triangle', 'points': points, 'width': random.randint(8, 16)}
    
    def _generate_curvilinear_primitive(self):
        x1 = random.randint(0, self.grid_size - 1) * self.cell_size + self.cell_size // 2
        y1 = random.randint(0, self.grid_size - 1) * self.cell_size + self.cell_size // 2
        x2 = random.randint(0, self.grid_size - 1) * self.cell_size + self.cell_size // 2
        y2 = random.randint(0, self.grid_size - 1) * self.cell_size + self.cell_size // 2
        
        cx = (x1 + x2) // 2 + random.randint(-self.cell_size, self.cell_size)
        cy = (y1 + y2) // 2 + random.randint(-self.cell_size, self.cell_size)
        
        return {'type': 'curve', 'coords': [(x1, y1), (cx, cy), (x2, y2)], 'width': random.randint(8, 16)}
    
    def _generate_angular_primitive(self):
        points = []
        segments = random.randint(2, 4)
        for i in range(segments):
            x = random.randint(0, self.grid_size - 1) * self.cell_size + self.cell_size // 2
            y = random.randint(0, self.grid_size - 1) * self.cell_size + self.cell_size // 2
            points.append((x, y))
        return {'type': 'polyline', 'points': points, 'width': random.randint(8, 16)}
    
    def _generate_mixed_primitive(self):
        choice = random.choice(['geometric', 'curvilinear', 'angular'])
        if choice == 'geometric':
            return self._generate_geometric_primitive()
        elif choice == 'curvilinear':
            return self._generate_curvilinear_primitive()
        else:
            return self._generate_angular_primitive()
    
    def _draw_primitive(self, draw, primitive, symmetry):
        color = (0, 0, 0, 255)
        
        if primitive['type'] == 'line':
            draw.line(primitive['coords'], fill=color, width=primitive['width'])
            if symmetry in ['vertical', 'both']:
                mirrored = self._mirror_horizontal(primitive['coords'])
                draw.line(mirrored, fill=color, width=primitive['width'])
            if symmetry in ['horizontal', 'both']:
                mirrored = self._mirror_vertical(primitive['coords'])
                draw.line(mirrored, fill=color, width=primitive['width'])
        
        elif primitive['type'] == 'circle':
            cx, cy = primitive['center']
            r = primitive['radius']
            bbox = [cx - r, cy - r, cx + r, cy + r]
            draw.ellipse(bbox, outline=color, width=primitive['width'])
            if symmetry in ['vertical', 'both']:
                mcx = self.size - cx
                bbox = [mcx - r, cy - r, mcx + r, cy + r]
                draw.ellipse(bbox, outline=color, width=primitive['width'])
            if symmetry in ['horizontal', 'both']:
                mcy = self.size - cy
                bbox = [cx - r, mcy - r, cx + r, mcy + r]
                draw.ellipse(bbox, outline=color, width=primitive['width'])
        
        elif primitive['type'] == 'triangle':
            draw.polygon(primitive['points'], outline=color, width=primitive['width'])
            if symmetry in ['vertical', 'both']:
                mirrored = [self._mirror_point_h(p) for p in primitive['points']]
                draw.polygon(mirrored, outline=color, width=primitive['width'])
            if symmetry in ['horizontal', 'both']:
                mirrored = [self._mirror_point_v(p) for p in primitive['points']]
                draw.polygon(mirrored, outline=color, width=primitive['width'])
        
        elif primitive['type'] == 'curve':
            self._draw_bezier(draw, primitive['coords'], color, primitive['width'])
            if symmetry in ['vertical', 'both']:
                mirrored = [self._mirror_point_h(p) for p in primitive['coords']]
                self._draw_bezier(draw, mirrored, color, primitive['width'])
            if symmetry in ['horizontal', 'both']:
                mirrored = [self._mirror_point_v(p) for p in primitive['coords']]
                self._draw_bezier(draw, mirrored, color, primitive['width'])
        
        elif primitive['type'] == 'polyline':
            for i in range(len(primitive['points']) - 1):
                draw.line([primitive['points'][i], primitive['points'][i + 1]], 
                         fill=color, width=primitive['width'])
            if symmetry in ['vertical', 'both']:
                mirrored = [self._mirror_point_h(p) for p in primitive['points']]
                for i in range(len(mirrored) - 1):
                    draw.line([mirrored[i], mirrored[i + 1]], fill=color, width=primitive['width'])
            if symmetry in ['horizontal', 'both']:
                mirrored = [self._mirror_point_v(p) for p in primitive['points']]
                for i in range(len(mirrored) - 1):
                    draw.line([mirrored[i], mirrored[i + 1]], fill=color, width=primitive['width'])
    
    def _draw_bezier(self, draw, points, color, width):
        steps = 30
        coords = []
        for t in range(steps + 1):
            t_norm = t / steps
            x = ((1 - t_norm) ** 2) * points[0][0] + 2 * (1 - t_norm) * t_norm * points[1][0] + (t_norm ** 2) * points[2][0]
            y = ((1 - t_norm) ** 2) * points[0][1] + 2 * (1 - t_norm) * t_norm * points[1][1] + (t_norm ** 2) * points[2][1]
            coords.append((int(x), int(y)))
        
        for i in range(len(coords) - 1):
            draw.line([coords[i], coords[i + 1]], fill=color, width=width)
    
    def _mirror_horizontal(self, coords):
        return [(self.size - x, y) for x, y in coords]
    
    def _mirror_vertical(self, coords):
        return [(x, self.size - y) for x, y in coords]
    
    def _mirror_point_h(self, point):
        return (self.size - point[0], point[1])
    
    def _mirror_point_v(self, point):
        return (point[0], self.size - point[1])
    
    def generate_alphabet(self, chars, complexity_map=None):
        glyphs = {}
        for i, char in enumerate(chars):
            complexity = complexity_map.get(char, 5) if complexity_map else 5
            glyphs[char] = self.generate_glyph(char, complexity)
        return glyphs
