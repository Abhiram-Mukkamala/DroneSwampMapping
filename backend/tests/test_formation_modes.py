import math

    def test_beta_default_parameters(self):
        controller = create_controller()
        red_pos = controller.red_pos
        controller.set_formation("beta")
        targets = controller.targets

        xs = [t[0] for t in targets]
        ys = [t[1] for t in targets]
        zs = [t[2] for t in targets]

        self.assertAlmostEqual(sum(xs) / len(xs), red_pos[0], places=5)
        self.assertAlmostEqual(sum(ys) / len(ys), red_pos[1], places=5)

        for z in zs:
            self.assertAlmostEqual(z, red_pos[2], places=5)

    def test_gamma_default_parameters(self):
        controller = create_controller()
        red_pos = controller.red_pos
        controller.set_formation("gamma")
        targets = controller.targets

        xs = [t[0] for t in targets]
        ys = [t[1] for t in targets]
        zs = [t[2] for t in targets]

        self.assertAlmostEqual(sum(xs) / len(xs), red_pos[0], places=5)
        self.assertAlmostEqual(sum(ys) / len(ys), red_pos[1], places=5)

        for z in zs:
            self.assertAlmostEqual(z, red_pos[2], places=5)

        distances = [
            math.sqrt((x - red_pos[0]) ** 2 + (y - red_pos[1]) ** 2)
            for x, y in zip(xs, ys)
        ]
        self.assertAlmostEqual(min(distances), max(distances), places=5)