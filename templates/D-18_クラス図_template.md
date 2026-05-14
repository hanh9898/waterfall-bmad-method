# D-18 クラス図

## 1. 概要
- **ID**: 
- **名称**: 
- **概要**: (このクラス図が示す範囲や目的を記述します)

## 2. クラス図

> [!NOTE]
> クラスの静的な構造、関連、継承などをPlantUMLまたはMermaidのクラス図で記述します。

```plantuml
@startuml
class ClassA {
  - field1: String
  # field2: int
  + method1(): void
  # method2(): String
}

class ClassB {
  + methodB(): void
}

note right on link: ClassA "1" -- "0..*" ClassB : uses

ClassA --|> ClassC : extends
ClassD ..|> InterfaceA : implements
@enduml
```

## 3. クラス定義
(クラス図だけでは伝わらない各クラスの詳細な情報を記述します)

### 3.1. ClassA
- **概要**:
- **責務**:
- **主要なプロパティ**:
  | 修飾子 | 名称 | 型 | 説明 |
  |---|---|---|---|
  | - | field1 | String | |
  | # | field2 | int | |
- **主要なメソッド**:
  | 修飾子 | 名称 | 引数 | 戻り値 | 説明 |
  |---|---|---|---|---|
  | + | method1 | | void | |
  | # | method2 | | String | |

---

**改訂履歴**

| 日付 | バージョン | 改訂内容 | 担当者 |
|---|---|---|---|
| yyyy-mm-dd | 1.0 | 初版作成 | |
