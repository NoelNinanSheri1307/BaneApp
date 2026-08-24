import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:bane/main.dart';

void main() {
  testWidgets('BaneApp renders landing screen smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: BaneApp(),
      ),
    );
    await tester.pump(const Duration(milliseconds: 500));
    expect(find.textContaining('BIOMEDICAL RESEARCH'), findsWidgets);
  });
}
