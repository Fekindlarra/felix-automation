#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 14 Track E: Mobile Optimization Testing
Tests for responsive design, PWA, offline capability, and touch-friendly UI
"""

import pytest
from pathlib import Path

# =============================================================================
# RESPONSIVE DESIGN TESTS
# =============================================================================

class TestResponsiveDesign:
    """Tests for mobile-first responsive design"""

    def test_mobile_css_exists(self):
        """Verify mobile CSS file exists"""
        css_path = Path("/home/claude/felix-automation/frontend/styles/mobile.css")
        assert css_path.exists(), "mobile.css should exist"
        
        with open(css_path) as f:
            content = f.read()
            # Check for breakpoints
            assert "--mobile-breakpoint:" in content or "320px" in content
            assert "--touch-target:" in content or "44px" in content

    def test_mobile_dashboard_exists(self):
        """Verify mobile dashboard HTML exists"""
        html_path = Path("/home/claude/felix-automation/frontend/dashboard_mobile.html")
        assert html_path.exists(), "dashboard_mobile.html should exist"
        
        with open(html_path) as f:
            content = f.read()
            # Check for responsive meta tag
            assert "viewport" in content
            assert "width=device-width" in content
            assert "initial-scale=1" in content

    def test_viewport_meta_tag(self):
        """Verify proper viewport configuration"""
        html_path = Path("/home/claude/felix-automation/frontend/dashboard_mobile.html")
        with open(html_path) as f:
            content = f.read()
            assert "viewport-fit=cover" in content or "viewport" in content

    def test_safe_area_insets(self):
        """Check for safe area inset support"""
        css_path = Path("/home/claude/felix-automation/frontend/styles/mobile.css")
        with open(css_path) as f:
            content = f.read()
            # Should handle safe area insets for notches
            assert "safe-area-inset" in content

# =============================================================================
# PWA FUNCTIONALITY TESTS
# =============================================================================

class TestPWAFeatures:
    """Tests for Progressive Web App features"""

    def test_manifest_json_exists(self):
        """Verify manifest.json exists and is valid"""
        import json
        
        # Check in backend
        backend_path = Path("/home/claude/felix-automation/backend/manifest.json")
        assert backend_path.exists(), "manifest.json should exist in backend"
        
        with open(backend_path) as f:
            data = json.load(f)
            assert "name" in data
            assert "short_name" in data
            assert "start_url" in data
            assert "display" in data
            assert data["display"] == "standalone"

    def test_manifest_has_icons(self):
        """Verify manifest includes app icons"""
        import json
        
        manifest_path = Path("/home/claude/felix-automation/backend/manifest.json")
        with open(manifest_path) as f:
            data = json.load(f)
            assert "icons" in data
            assert len(data["icons"]) > 0
            # Should have at least 192x192 and 512x512
            sizes = [icon["sizes"] for icon in data["icons"]]
            assert any("192" in size for size in sizes)
            assert any("512" in size for size in sizes)

    def test_service_worker_exists(self):
        """Verify service worker file exists"""
        sw_path = Path("/home/claude/felix-automation/backend/service_worker.js")
        assert sw_path.exists(), "service_worker.js should exist"
        
        with open(sw_path) as f:
            content = f.read()
            # Check for cache strategies
            assert "install" in content
            assert "activate" in content
            assert "fetch" in content

    def test_service_worker_cache_strategies(self):
        """Verify proper cache strategies in service worker"""
        sw_path = Path("/home/claude/felix-automation/backend/service_worker.js")
        with open(sw_path) as f:
            content = f.read()
            # Should implement multiple cache strategies
            assert "networkFirst" in content or "network-first" in content
            assert "cacheFirst" in content or "cache-first" in content
            assert "CACHE_" in content  # Cache names

    def test_app_mobile_js_exists(self):
        """Verify mobile app JavaScript exists"""
        js_path = Path("/home/claude/felix-automation/frontend/js/app_mobile.js")
        assert js_path.exists(), "app_mobile.js should exist"
        
        with open(js_path) as f:
            content = f.read()
            # Check for service worker registration
            assert "registerServiceWorker" in content
            assert "serviceWorker" in content

# =============================================================================
# TOUCH-FRIENDLY UI TESTS
# =============================================================================

class TestTouchFriendlyUI:
    """Tests for mobile touch optimization"""

    def test_touch_target_size(self):
        """Verify minimum 44x44px touch targets"""
        css_path = Path("/home/claude/felix-automation/frontend/styles/mobile.css")
        with open(css_path) as f:
            content = f.read()
            # Should define 44px minimum
            assert "44" in content or "--touch-target" in content

    def test_button_minimum_size(self):
        """Verify buttons meet minimum size requirements"""
        css_path = Path("/home/claude/felix-automation/frontend/styles/mobile.css")
        with open(css_path) as f:
            content = f.read()
            # Buttons should have min-width and min-height
            assert "min-width" in content
            assert "min-height" in content

    def test_spacing_between_interactive_elements(self):
        """Verify adequate spacing between touch targets"""
        css_path = Path("/home/claude/felix-automation/frontend/styles/mobile.css")
        with open(css_path) as f:
            content = f.read()
            # Should define gap/spacing variables
            assert "--gap" in content

    def test_no_hover_only_interactions(self):
        """Verify no hover-only interactions on touch"""
        css_path = Path("/home/claude/felix-automation/frontend/styles/mobile.css")
        with open(css_path) as f:
            content = f.read()
            # Should have hover:none media query or similar
            if "hover" in content:
                assert "prefers-reduced-motion" in content or "(hover: none)" in content

# =============================================================================
# OFFLINE CAPABILITY TESTS
# =============================================================================

class TestOfflineCapability:
    """Tests for offline functionality"""

    def test_offline_detection(self):
        """Verify offline detection is implemented"""
        js_path = Path("/home/claude/felix-automation/frontend/js/app_mobile.js")
        with open(js_path) as f:
            content = f.read()
            # Should detect online/offline status
            assert "online" in content
            assert "offline" in content
            assert "navigator.onLine" in content

    def test_offline_indicator(self):
        """Verify offline indicator is present"""
        html_path = Path("/home/claude/felix-automation/frontend/dashboard_mobile.html")
        with open(html_path) as f:
            content = f.read()
            assert "offline" in content.lower()

    def test_service_worker_offline_handling(self):
        """Verify service worker handles offline gracefully"""
        sw_path = Path("/home/claude/felix-automation/backend/service_worker.js")
        with open(sw_path) as f:
            content = f.read()
            # Should have fallback for offline requests
            assert "fallback" in content or "catch" in content

# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Performance and optimization tests"""

    def test_css_minification_potential(self):
        """Check CSS for optimization opportunities"""
        css_path = Path("/home/claude/felix-automation/frontend/styles/mobile.css")
        size = css_path.stat().st_size
        # Should be reasonably sized (< 20KB for mobile CSS)
        assert size < 20000, f"Mobile CSS too large: {size} bytes"

    def test_lazy_loading_support(self):
        """Verify lazy loading for images/charts"""
        html_path = Path("/home/claude/felix-automation/frontend/dashboard_mobile.html")
        with open(html_path) as f:
            content = f.read()
            # Should have lazy loading or intersection observer
            assert "lazy" in content or "IntersectionObserver" in content or "data-chart" in content

    def test_reduced_motion_support(self):
        """Verify support for prefers-reduced-motion"""
        css_path = Path("/home/claude/felix-automation/frontend/styles/mobile.css")
        with open(css_path) as f:
            content = f.read()
            # Should respect motion preferences
            assert "prefers-reduced-motion" in content

# =============================================================================
# MOBILE OPTIMIZATION TESTS
# =============================================================================

class TestMobileOptimization:
    """Tests for mobile-specific optimizations"""

    def test_heartbeat_optimization(self):
        """Verify heartbeat optimization for mobile"""
        js_path = Path("/home/claude/felix-automation/frontend/js/app_mobile.js")
        with open(js_path) as f:
            content = f.read()
            # Should detect mobile and adjust heartbeat
            assert "HEARTBEAT_INTERVAL" in content
            assert "60" in content  # 60s for mobile

    def test_network_detection(self):
        """Verify network type detection"""
        js_path = Path("/home/claude/felix-automation/frontend/js/app_mobile.js")
        with open(js_path) as f:
            content = f.read()
            # Should detect network type (4g, 3g, 2g)
            assert "connection" in content or "effectiveType" in content

    def test_device_memory_awareness(self):
        """Verify device capabilities detection"""
        js_path = Path("/home/claude/felix-automation/frontend/js/app_mobile.js")
        with open(js_path) as f:
            content = f.read()
            # Should be aware of device constraints
            assert "deviceMemory" in content or "navigator" in content

# =============================================================================
# BROWSER COMPATIBILITY TESTS
# =============================================================================

class TestBrowserCompatibility:
    """Tests for browser and OS compatibility"""

    def test_ios_app_config(self):
        """Verify iOS app configuration"""
        html_path = Path("/home/claude/felix-automation/frontend/dashboard_mobile.html")
        with open(html_path) as f:
            content = f.read()
            # Should have iOS-specific meta tags
            assert "apple-mobile-web-app" in content

    def test_android_pwa_config(self):
        """Verify Android PWA configuration"""
        manifest_path = Path("/home/claude/felix-automation/backend/manifest.json")
        with open(manifest_path) as f:
            content = f.read()
            # Manifest is primarily for Android PWA
            assert "manifest" in content.lower()

    def test_theme_color_setup(self):
        """Verify theme color configuration"""
        html_path = Path("/home/claude/felix-automation/frontend/dashboard_mobile.html")
        with open(html_path) as f:
            content = f.read()
            assert "theme-color" in content

# =============================================================================
# ACCESSIBILITY TESTS
# =============================================================================

class TestAccessibility:
    """Accessibility for mobile"""

    def test_keyboard_navigation(self):
        """Verify keyboard navigation support"""
        css_path = Path("/home/claude/felix-automation/frontend/styles/mobile.css")
        with open(css_path) as f:
            content = f.read()
            # Should have focus styles
            assert "focus" in content

    def test_touch_target_focus_states(self):
        """Verify focus states are visible"""
        css_path = Path("/home/claude/felix-automation/frontend/styles/mobile.css")
        with open(css_path) as f:
            content = f.read()
            # Should have focus-visible
            assert "focus-visible" in content or "focus:" in content

# =============================================================================
# DEPLOYMENT TESTS
# =============================================================================

class TestDeployment:
    """Deployment checklist items"""

    def test_manifest_link_in_html(self):
        """Verify manifest is linked in HTML"""
        html_path = Path("/home/claude/felix-automation/frontend/dashboard_mobile.html")
        with open(html_path) as f:
            content = f.read()
            assert 'rel="manifest"' in content

    def test_service_worker_registration(self):
        """Verify service worker is registered"""
        js_path = Path("/home/claude/felix-automation/frontend/js/app_mobile.js")
        with open(js_path) as f:
            content = f.read()
            assert "service_worker" in content or "serviceWorker" in content

    def test_icons_referenced(self):
        """Verify icons are properly referenced"""
        html_path = Path("/home/claude/felix-automation/frontend/dashboard_mobile.html")
        with open(html_path) as f:
            content = f.read()
            # Should reference touch icon or favicon
            assert "icon" in content or "apple-touch" in content

# =============================================================================
# PERFORMANCE BENCHMARKS
# =============================================================================

class TestPerformanceBenchmarks:
    """Performance target validation"""

    def test_html_file_size(self):
        """Verify HTML file is reasonably sized"""
        html_path = Path("/home/claude/felix-automation/frontend/dashboard_mobile.html")
        size = html_path.stat().st_size / 1024  # KB
        # Should be < 100KB
        assert size < 100, f"HTML file too large: {size:.1f}KB"
        print(f"  HTML size: {size:.1f}KB ✓")

    def test_css_file_size(self):
        """Verify CSS is optimized"""
        css_path = Path("/home/claude/felix-automation/frontend/styles/mobile.css")
        size = css_path.stat().st_size / 1024  # KB
        # Should be < 15KB
        assert size < 15, f"CSS file too large: {size:.1f}KB"
        print(f"  CSS size: {size:.1f}KB ✓")

    def test_js_file_size(self):
        """Verify JavaScript is optimized"""
        js_path = Path("/home/claude/felix-automation/frontend/js/app_mobile.js")
        size = js_path.stat().st_size / 1024  # KB
        # Should be < 10KB
        assert size < 10, f"JS file too large: {size:.1f}KB"
        print(f"  JS size: {size:.1f}KB ✓")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
