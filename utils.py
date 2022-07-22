from tkinter import CENTER
import pygame

"""
Function for scaling an image by a factor (either makes the image smaller or bigger)
"""
def scale_image(img, factor):
    size = round(img.get_width() * factor), round(img.get_height() * factor)
    return pygame.transform.scale(img, size)


"""
Function for rotating an image in pygame without distortions
"""
def blit_rotate_center(win, image, top_left, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    # Rotate around the center of the image, without damaging x or y values
    new_rect = rotated_image.get_rect(center = image.get_rect(topleft = top_left).center)
    win.blit(rotated_image, new_rect.topleft)

"""
Function for displaying text on window
"""
def blit_text_center(win, font, text):
    # 1 is for anti-aliacing (always put 1), last parameter is RGB for text color
    render = font.render(text, 1, (200, 200, 200))

    # Show render at the center of the window (get x,y for top-left position of the render)
    win.blit(render, (win.get_width()/2 - render.get_width()/2, win.get_height()/2 - render.get_height()/2 - 30))