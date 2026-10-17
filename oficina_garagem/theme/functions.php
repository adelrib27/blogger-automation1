<?php
/** Styles and behavior for the reusable editorial child theme. */
add_action('wp_enqueue_scripts', function () {
    wp_enqueue_style('cd-editorial', get_stylesheet_uri(), array(), wp_get_theme()->get('Version'));
    if (is_home() || is_front_page()) {
        wp_enqueue_script('cd-editorial-carousel', get_stylesheet_directory_uri() . '/assets/carousel.js', array(), wp_get_theme()->get('Version'), true);
    }
});
