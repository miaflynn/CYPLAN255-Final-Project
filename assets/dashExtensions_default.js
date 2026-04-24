window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, context) {
            const {
                selected,
                low,
                high
            } = context.hideout;
            const isSelected = selected.includes(feature.properties.neighborhood);
            const bizStock = feature.properties.biz_stock;

            const norm = Math.min(Math.max((bizStock - low) / (high - low), 0), 1);
            const r = 255;
            const g = Math.round(165 * (1 - norm));
            const b = 0;

            return {
                fillColor: isSelected ? 'steelblue' : `rgb(${r},${g},${b})`,
                fillOpacity: isSelected ? 0.8 : 0.6,
                color: 'white',
                weight: 1
            };
        }

    }
});