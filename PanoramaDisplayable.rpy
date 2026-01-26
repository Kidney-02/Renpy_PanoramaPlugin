init python:

    renpy.register_shader("sphere_projection",
    variables="""
        uniform sampler2D background;
        uniform sampler2D layer_1;
        uniform sampler2D layer_2;
        uniform float layer_1_opacity;
        uniform float layer_2_opacity;
        varying vec2 v_tex_coord;
        uniform vec2 u_model_size;

        uniform vec2 offset;
        uniform float zoom;
        uniform int debug;
        uniform vec2 target;
        uniform vec2 target_range;        
    """,
    fragment_200="""
        vec2 uv = v_tex_coord - 0.5; // Center UV so 0,0 is in center for sphere projection
        uv.x *= u_model_size.x / u_model_size.y; // fix ratio
        uv *= zoom;  
        const float PI = 3.1415926535897932384626433832795;        

        float yaw = (offset.x) * 2 * PI;   // Horizontal rotation
        float pitch = (offset.y - 0.5) * PI; // Vertical rotation

        // Ray direction - View Direction
        vec3 rd = normalize(vec3(uv, 1.0));    

        float cp = cos(pitch), sp = sin(pitch);
        rd.yz *= mat2(cp, -sp, sp, cp);
        float cy = cos(yaw), sy = sin(yaw);
        rd.xz *= mat2(cy, -sy, sy, cy);


        float phi = atan(rd.z, rd.x);
        float theta = asin(rd.y);
        vec2 sphere_uv = vec2(phi / (-2*PI) + 0.25, theta / PI + 0.5);

        vec4 col = texture2D(background, sphere_uv, 0.).rgba;

        vec4 col_1 = texture2D(layer_1, sphere_uv, 0.).rgba;
        col.rgb = mix(col.rgb, col_1.rgb, clamp(layer_1_opacity * col_1.a,0.,1.));
        
        vec4 col_2 = texture2D(layer_2, sphere_uv, 0.).rgba;        
        col.rgb = mix(col.rgb, col_2.rgb, clamp(layer_2_opacity * col_2.a,0.,1.));


        if (debug == 1) {       
            // Draw Square on Sphere UV
            vec3 offset_color = vec3(0., 0., 1.);            
            vec3 target_color = vec3(1., 0., 0.);

            float o_circ = clamp((0.002 - distance(vec2(0.5,0.5), v_tex_coord)) * 10000., 0., 1.);
            bool t_rect = false;

            vec2 inv_target = vec2(1.,1.) - target;
            vec2 centered_uv = abs(mod(sphere_uv, 1.) - inv_target );

            if (all(lessThan(centered_uv, target_range * 0.5))){
                t_rect = true;
            }

            col.rgb = mix(col.rgb, target_color, float(t_rect));
            col.rgb = mix(col.rgb, offset_color, o_circ);
            //col.rgb = vec3(centered_uv, 0.);
        }
        else if (debug == 2 || debug == 3) {         
            // Draw Square in Screen UV   
            vec3 offset_color = vec3(0., 0., 1.);            
            vec3 target_color = vec3(1., 0., 0.);

            float o_circ = clamp((0.002 - distance(offset, v_tex_coord)) * 10000., 0., 1.);
            bool t_rect = false;

            if (all(greaterThan(v_tex_coord, target - (target_range * 0.5))) && all(lessThan(v_tex_coord, target + (target_range * 0.5)))){
                t_rect = true;
            }

            if (debug == 3){
                col.rgb = texture2D(background, v_tex_coord, 0.).rgb;
            }

            col.rgb = mix(col.rgb, target_color, float(t_rect));
            col.rgb = mix(col.rgb, offset_color, o_circ);
        }

        gl_FragColor = col;
    """)

    import pygame
    from operator import sub, add, mul, mod
    from math import dist, pi, cos
    from renpy.uguu import GL_REPEAT, GL_NEAREST

    class Panorama(renpy.Displayable):

        def __init__(self, background:str, targets:dict,
                layer_1:str = None, layer_2:str = None,
                alpha_1:float = 0., alpha_2:float = 0., 
                offset:tuple = (0.0,0.5),
                callback = None, screen:str = None,
                speed:tuple = (0.2,0.2), frame_clamp:float = 0, zoom:float = 1
                ):
            """
            Panorama displayable

            background - Name of background layer image;
            targets - Dictionary of targets format - {Target_Name : Target_Coord.X, Target_Coord.Y, Target_Width, Target_Height};
            layer_1 - Name of layer 1 image (include extension);
            layer_2 - Name of layer 2 image (include extension);
            alpha_1 - Opacity of layer 1 on startup;
            alpha_2 - Opacity of layer 2 on startup;
            offset - Coordinate where player is looking at creation of displayable (0 or 1 on X are on the edge of the image, 0.5 on Y is looking at middle of the image);
            callback - Function to call when any active target is hit;
            screen - Name of a screen to be passed to the callback function. Use to track the parent of the displayable;
            speed - How fast the mouse moves the screen. Separate for X and Y. Default - (0.2, 0.2);
            frame_clamp - The maximum movement a mouse can do per frame ignore if 0;
            zoom - Zoom in or out to panorama. 1 - default zoom. < 1 zooms in, > 1 zooms out. Negative values invert the image;
            """
            renpy.Displayable.__init__(self)
            # self.background:str         = background
            self.background = renpy.displayable(background)

            self.layer = [0] * 2
            self.alpha = [0] * 2
            self.layer[0] = renpy.displayable(layer_1) if layer_1 is not None else self.background
            self.layer[1] = renpy.displayable(layer_2) if layer_2 is not None else self.background
            self.alpha[0]:float = alpha_1
            self.alpha[1]:float = alpha_2

            self.offset:tuple           = offset
            self.speed:tuple            = speed
            self.frame_clamp:float      = frame_clamp  # Used to clamp maximum frame rotation after speed is applied
            self.zoom:float             = zoom

            
            self.targets:dict           = {}
            # Calculate target bounds and remake targets 
            # dict {name: [0]target, [1]bounds_min, [2]bounds_max, [3]Old_Range, [4]active_status}
            for name, value in targets.items():
                t_coord = (value[0],  value[1])
                bbox_range = (value[2] * 0.5,  value[3] * 0.5)
                min_corner = tuple(map(sub, t_coord, bbox_range))
                max_corner = tuple(map(add, t_coord, bbox_range))
                self.targets[name] = [t_coord, min_corner, max_corner, (value[2], value[3]), value[4]]

            self.callback:function      = callback
            self.screen:str             = screen

            self.is_dragging:bool       = False
            self.last_mouse_pos:tuple   = (0.,0.)
            
            self.animated:bool          = False
            self.anim_duration:float    = 2.
            self.anim_target:tuple      = (0,0)
            self.anim_start:float       = None
            self.anim_start_pos:tuple   = (0,0)
            
            self.interactable           = True

            # Debug Mode
            self.DEBUG:int              = 1
            self.DEBUG_TARGET:int       = "Target_50"
            self.debug_validate()
            pass


        def render(self, width, height, st, at):

            # Update logic happens here (Avoids rubberbanding that happens in def event())
            if self.is_dragging and not self.animated:
                # Mouse drag logic
                mouse_pos = self.calc_mouse_pos()
                delta = tuple(map(sub, mouse_pos, self.last_mouse_pos))
                scaled_delta = tuple(map(mul, delta, self.speed))
                
                # Clamp frame delta
                if self.frame_clamp is not 0:
                    scaled_delta_x = max(min(scaled_delta[0], self.frame_clamp), -self.frame_clamp)
                    scaled_delta_y = max(min(scaled_delta[1], self.frame_clamp), -self.frame_clamp)
                    scaled_delta = (scaled_delta_x,scaled_delta_y)
                
                new_x = ((self.offset[0] + scaled_delta[0]) + 1 ) % 1.0
                new_y = max(min(self.offset[1] + scaled_delta[1], 0.95), 0.05)                
                
                self.offset = (new_x, new_y)

                # Rect Test
                for name, value in self.targets.items():
                    if value[4] is not True:
                        continue
                    target = value[0]
                    bbox_min = value[1]
                    bbox_max = value[2]

                    # Check if offset is in bounds           
                    if all(map(lambda a, b: a > b,self.offset,bbox_min)) and all(map(lambda a, b: a < b,self.offset,bbox_max)):
                        # Check if entered bbox from left or right
                        # True if Right, False if Left 
                        direction = True if self.offset[0] < target[0] else False

                        # self.is_dragging = False
                        if self.callback is not None:
                            self.callback({
                                "self": self,
                                "screen": self.screen,
                                "target": name,
                                "direction": direction,
                                "offset": self.offset
                            })

                # Sync mouse position
                self.last_mouse_pos = mouse_pos

            elif not self.is_dragging and self.animated:
                # Animation logic
                if self.anim_start is None:
                    self.anim_start = st
                    self.anim_start_pos = self.offset
                
                # Calculate progress (0.0 to 1.0)
                elapsed = st - self.anim_start
                progress = min(elapsed / self.anim_duration, 1.0)

                # Smoothstep makes the movement start and end soft
                # t = progress * progress * (3.0 - 2.0 * progress)
                t = cos((progress + 1) * pi) * 0.5 + 0.5

                # Interpolate X and Y
                new_x = self.anim_start_pos[0] + (self.anim_target[0] - self.anim_start_pos[0]) * t
                new_y = self.anim_start_pos[1] + (self.anim_target[1] - self.anim_start_pos[1]) * t

                self.offset = (new_x, new_y)

                # If animation finished
                if t == 1:
                    self.animated = False
                    self.interactable = True

                pass


            # Actual Render Parameters
            render = renpy.Render(width, height)

            # Create a rect to cover the screen for proper UV coordinates
            render.canvas().rect("#00000000", (0, 0, width, height))

            # render.add_uniform("background", renpy.render(renpy.displayable(self.background), width, height, st, at))
            render.add_uniform("background", renpy.render(self.background, width, height, st, at))
            render.add_uniform("layer_1", renpy.render(self.layer[0], width, height, st, at))
            render.add_uniform("layer_1_opacity", self.alpha[0])
            render.add_uniform("layer_2", renpy.render(self.layer[1], width, height, st, at))
            render.add_uniform("layer_2_opacity", self.alpha[1])
            render.add_uniform("zoom", self.zoom)
            render.add_uniform("offset", self.offset)

            render.add_uniform("debug", 1)
            render.add_uniform("target", self.targets[self.DEBUG_TARGET][0])
            render.add_uniform("target_range", self.targets[self.DEBUG_TARGET][3])
            
            render.add_property("gl_texture_wrap", (GL_REPEAT, GL_REPEAT))
            render.add_property("gl_mipmap", False)
            render.add_property("gl_mag_filter", GL_NEAREST)
            render.add_property("gl_min_filter", GL_NEAREST)
            
            render.add_shader("sphere_projection")

            renpy.redraw(self, 0)

            return render


        def event(self, ev, x, y, st):
            """
            Process mouse click events
            """
            if self.interactable == False:
                return
            # Track ONLY the mouse state here
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self.is_dragging = True
               
                self.last_mouse_pos = self.calc_mouse_pos()
                # renpy.redraw(self, 0)
                raise renpy.display.core.IgnoreEvent()

            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self.is_dragging = False


        def calc_mouse_pos(self) -> tuple:
            """
            Calculate mouse position relative to the game screen
            """
            w, h = renpy.config.screen_width, renpy.config.screen_height
            x, y = pygame.mouse.get_pos()
            mouse_pos = (x / w, y / h)
            
            return mouse_pos


        def set_taget_status(self, target:str, new_status:bool):
            """
            Set active status of a particular target
            
            target - Target Name;
            new_status - Activity Status;
            """
            target_value = self.targets[target]
            self.targets.update({target: (target_value[0], target_value[1], target_value[2], target_value[3], new_status)})
            pass


        def set_callback(self, callback):
            """
            Set callback function from outside

            callback - new callback function;
            """            
            self.callback = callback


        def anim_to_target(self, target:str, total_time:float):
            """
            Start animation from outside

            target - name of target to animate to;
            total_time - duration of animation;
            """
            self.animated = True
            self.interactable = False
            self.is_dragging = False
            self.anim_duration = total_time
            self.anim_target = self.targets[target][0]
            pass


        def set_layer_alpha(self, layer:int, alpha:float):
            """
            Set Specific layer opacity

            layer - number of layer to edit
            alpha - opacity value for the layer
            """
            self.alpha[layer] = alpha
            pass


        def debug_validate(self):
            
            if self.DEBUG_TARGET not in self.targets.keys():
                keys = list(self.targets.keys())
                self.DEBUG_TARGET = keys[0]