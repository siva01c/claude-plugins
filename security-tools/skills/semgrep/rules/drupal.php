<?php

/**
 * @file
 * Test fixture for rules/drupal.yml — run with `semgrep --test rules/`.
 *
 * Every `ruleid:` comment marks the next line as a line the rule must report,
 * every `ok:` comment marks the next line as one it must not report.
 */

namespace Drupal\fixture\Controller;

use Drupal\Component\Utility\Html;
use Drupal\Component\Utility\Xss;
use Drupal\Core\Controller\ControllerBase;
use Drupal\Core\Database\Connection;
use Drupal\Core\Render\Markup;
use Symfony\Component\DependencyInjection\ContainerInterface;
use Symfony\Component\HttpFoundation\Request;

/**
 * SQL injection: drupal-sqli-concatenated-query.
 */
class SqlController extends ControllerBase {

  public function __construct(protected Connection $connection) {}

  public static function create(ContainerInterface $container) {
    return new static($container->get('database'));
  }

  public function concatenated(string $title) {
    // ruleid: drupal-sqli-concatenated-query
    return $this->connection->query("SELECT nid FROM {node_field_data} WHERE title = '" . $title . "'");
  }

  public function interpolated(string $title) {
    // ruleid: drupal-sqli-concatenated-query
    return $this->connection->query("SELECT nid FROM {node_field_data} WHERE title = '$title'");
  }

  public function formatted(string $title) {
    // ruleid: drupal-sqli-concatenated-query
    return $this->connection->query(sprintf("SELECT nid FROM {node_field_data} WHERE title = '%s'", $title));
  }

  public function legacy(string $title) {
    // ruleid: drupal-sqli-concatenated-query
    return db_query('SELECT nid FROM {node_field_data} WHERE title = ' . $title);
  }

  public function placeholder(string $title) {
    // ok: drupal-sqli-concatenated-query
    return $this->connection->query('SELECT nid FROM {node_field_data} WHERE title = :title', [':title' => $title]);
  }

  public function builder(string $title) {
    // ok: drupal-sqli-concatenated-query
    return $this->connection->select('node_field_data', 'n')->fields('n', ['nid'])->condition('title', $title)->execute();
  }

}

/**
 * XSS: drupal-xss-markup-unescaped and drupal-xss-markup-create.
 */
class MarkupController extends ControllerBase {

  public function variable(Request $request) {
    $name = $request->query->get('name');
    // ruleid: drupal-xss-markup-unescaped
    $build = ['#markup' => $name];
    // ruleid: drupal-xss-markup-unescaped
    $build['#markup'] = '<p>' . $name . '</p>';
    // ruleid: drupal-xss-markup-unescaped
    $build['greeting'] = ['#type' => 'markup', '#markup' => "Hello $name"];
    // ok: drupal-xss-markup-unescaped
    $build['static'] = ['#markup' => '<p>Static text</p>'];
    // ok: drupal-xss-markup-unescaped
    $build['translated'] = ['#markup' => $this->t('Hello @name', ['@name' => $name])];
    // ok: drupal-xss-markup-unescaped
    $build['filtered'] = ['#markup' => Xss::filter($name)];
    // ok: drupal-xss-markup-unescaped
    $build['#markup'] = Html::escape($name);
    // ok: drupal-xss-markup-unescaped
    $build['plain'] = ['#plain_text' => $name];
    return $build;
  }

  public function created(string $html) {
    // ruleid: drupal-xss-markup-create
    $markup = Markup::create($html);
    // ruleid: drupal-xss-markup-create
    $markup = Markup::create('<div>' . $html . '</div>');
    // ok: drupal-xss-markup-create
    $markup = Markup::create('<br>');
    // ok: drupal-xss-markup-create
    $markup = Markup::create(Xss::filterAdmin($html));
    return $markup;
  }

}

/**
 * Superglobals: drupal-superglobal-access.
 */
function fixture_superglobals(Request $request) {
  // ruleid: drupal-superglobal-access
  $id = $_GET['id'];
  // ruleid: drupal-superglobal-access
  $body = $_POST['body'];
  // ruleid: drupal-superglobal-access
  $all = $_REQUEST;
  // ok: drupal-superglobal-access
  $id = $request->query->get('id');
  return [$id, $body, $all];
}

/**
 * Static service calls in a class with DI: drupal-static-call-in-di-class.
 */
class InjectedService {

  public function __construct(protected Connection $connection) {}

  public function run() {
    // ruleid: drupal-static-call-in-di-class
    $user = \Drupal::currentUser();
    // ruleid: drupal-static-call-in-di-class
    \Drupal::service('logger.factory')->get('fixture')->notice('run');
    // ruleid: drupal-static-call-in-di-class
    $renderer = \drupal::service('renderer');
    // ok: drupal-static-call-in-di-class
    return $this->connection->select('users', 'u')->countQuery()->execute();
  }

}

class ContainerFactory extends ControllerBase {

  public static function create(ContainerInterface $container) {
    // ok: drupal-static-call-in-di-class
    $config = \Drupal::config('system.site');
    return new static();
  }

  public function build() {
    // ruleid: drupal-static-call-in-di-class
    $request = \Drupal::request();
    return ['#plain_text' => $request->getPathInfo()];
  }

}

/**
 * Implements hook_help(); procedural code has no container to inject from.
 */
function fixture_help($route_name) {
  // ok: drupal-static-call-in-di-class
  return \Drupal::service('renderer')->renderPlain($route_name);
}

/**
 * Debug output: drupal-debug-output.
 */
function fixture_debug($data) {
  // ruleid: drupal-debug-output
  var_dump($data);
  // ruleid: drupal-debug-output
  print_r($data);
  // ruleid: drupal-debug-output
  dpm($data);
  // ruleid: drupal-debug-output
  kint($data);
  // ruleid: drupal-debug-output
  dump($data);
  // ok: drupal-debug-output
  $logged = print_r($data, TRUE);
  // ok: drupal-debug-output
  \Drupal::logger('fixture')->debug('@data', ['@data' => $logged]);
}
