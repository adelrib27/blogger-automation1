<?php
/**
 * Plugin Name: Radar Automation Bridge
 * Description: Ponte REST reutilizável para automações seguras nos sites WordPress do domínio radartechbr.com.br.
 * Version: 1.0.0
 * Author: Radar Tech BR
 */

if (!defined('ABSPATH')) {
    exit;
}

add_action('rest_api_init', function () {
    $ns = 'radar-automation/v1';

    register_rest_route($ns, '/health', [
        'methods'  => 'GET',
        'callback' => function () {
            return rest_ensure_response([
                'ok'       => true,
                'site'     => home_url('/'),
                'time_gmt' => current_time('mysql', true),
                'bridge'   => 'radar-automation-v1',
            ]);
        },
        'permission_callback' => '__return_true',
    ]);

    register_rest_route($ns, '/site', [
        'methods'  => 'GET',
        'callback' => function () {
            global $wp_version;
            $theme = wp_get_theme();
            $user  = wp_get_current_user();

            return rest_ensure_response([
                'name'       => get_bloginfo('name'),
                'url'        => home_url('/'),
                'rest_url'   => rest_url(),
                'wordpress'  => $wp_version,
                'php'        => PHP_VERSION,
                'theme'      => [
                    'name'       => $theme->get('Name'),
                    'version'    => $theme->get('Version'),
                    'stylesheet' => $theme->get_stylesheet(),
                ],
                'user'       => [
                    'id'    => get_current_user_id(),
                    'login' => $user->user_login,
                ],
            ]);
        },
        'permission_callback' => function () {
            return current_user_can('read');
        },
    ]);

    register_rest_route($ns, '/status', [
        'methods'  => 'GET',
        'callback' => function () {
            return rest_ensure_response([
                'site_url'            => site_url('/'),
                'home_url'            => home_url('/'),
                'is_multisite'        => is_multisite(),
                'timezone'            => wp_timezone_string(),
                'permalink_structure' => get_option('permalink_structure'),
                'blog_public'         => (bool) get_option('blog_public'),
                'posts_published'     => (int) wp_count_posts('post')->publish,
                'pages_published'     => (int) wp_count_posts('page')->publish,
            ]);
        },
        'permission_callback' => function () {
            return current_user_can('read');
        },
    ]);

    register_rest_route($ns, '/plugins', [
        'methods'  => 'GET',
        'callback' => function () {
            if (!function_exists('get_plugins')) {
                require_once ABSPATH . 'wp-admin/includes/plugin.php';
            }

            $all    = get_plugins();
            $active = (array) get_option('active_plugins', []);
            $out    = [];

            foreach ($all as $file => $data) {
                $out[] = [
                    'file'    => $file,
                    'name'    => $data['Name'] ?? $file,
                    'version' => $data['Version'] ?? '',
                    'active'  => in_array($file, $active, true),
                ];
            }

            return rest_ensure_response($out);
        },
        'permission_callback' => function () {
            return current_user_can('activate_plugins');
        },
    ]);

    register_rest_route($ns, '/cache/purge', [
        'methods'  => 'POST',
        'callback' => function () {
            $actions = [];

            wp_cache_flush();
            $actions[] = 'wp_cache_flush';

            if (has_action('litespeed_purge_all')) {
                do_action('litespeed_purge_all');
                $actions[] = 'litespeed_purge_all';
            }

            return rest_ensure_response([
                'ok'      => true,
                'actions' => $actions,
            ]);
        },
        'permission_callback' => function () {
            return current_user_can('manage_options');
        },
    ]);
});
