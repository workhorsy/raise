using System;
using MathHelper;

namespace Example {
	class MainClass {
		public static void Main(string[] args) {
			Console.WriteLine("3 + 22 == {0}", MathHelper.Funcs.Add(3, 22));
			Console.WriteLine("7 * 8 == {0}", MathHelper.Funcs.Multiply(7, 8));
		}
	}
}

